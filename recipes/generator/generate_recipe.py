import yaml
import os
import argparse

# -----------------------------------------------------------------------------
substitions = {
    "compiler": "${COMPILER}",
    "mpi": "${MPI}",
    "arch": "${ARCH}",
    "cluster": "${CLUSTER}",
    "variant": "${VARIANT}",
    "recipe": "${RECIPE}",
}


# -----------------------------------------------------------------------------
def substitute_vars(string):
    global arch, compiler, mpi, envname, cluster, variant, recipe, generated_path
    string = string.replace("${ARCH}", arch)
    string = string.replace("${COMPILER}", compiler)
    string = string.replace("${MPI}", mpi)
    string = string.replace("${ENVNAME}", envname)
    string = string.replace("${CLUSTER}", cluster)
    string = string.replace("${VARIANT}", variant)
    string = string.replace("${RECIPE}", recipe)
    string = string.replace("${GENERATED_DIR}", generated_path)
    return string


# -----------------------------------------------------------------------------
def check_key(key):
    for name, val in substitions.items():
        if key.startswith(f"{name}="):
            if key == f"{name}={substitute_vars(val)}":
                print(f"Substituting: {key:20} == {substitute_vars(val)}")
                return substitute_vars(val)
            elif key == f"{name}=else":
                print(f"Substituting: {key:20} else")
                return substitute_vars(val)
            else:
                print(f"Ignoring    : {key:20} != {substitute_vars(val)}")
                return None
    return key


# -----------------------------------------------------------------------------
def filter_items(data):
    if isinstance(data,list):
        return [item for item in (filter_items(item) for item in data) if item]

    elif isinstance(data,dict):
        new_dict = {}
        sub = [] # list of keys that have been substituted
        for k,v in data.items():
            new_key = check_key(k)
            if new_key is not None:
                if new_key != k:
                    if k not in sub: 
                        new_dict[k] = filter_items(v)
                        sub.append(k)
                else:
                    new_dict[k] = filter_items(v)
        return new_dict
    else:
        return data

# -----------------------------------------------------------------------------
def copy_recursive(data):
    new_data = filter_items(data)
    if isinstance(new_data, dict):
        result = {}
        for key, value in new_data.items():
            newkey = check_key(key)
            if newkey is None:
                print("SERIOUS ERROR #1")
                # drop this discarded value (eg wrong compiler/mpi/arch)
                continue
            else:
                if newkey == key:
                    # nothing changed, just copy through
                    result[key] = copy_recursive(value)
                else:
                    # substitution was made, we must copy all entries out of value and into this dict
                    if isinstance(value, dict):
                        new_value = copy_recursive(value)
                        for k, v in new_value.items():
                            if k not in result:
                                result[k] = v
                                print(f"result[{k}] = {result[k]}")

                    elif isinstance(value, list):
                        return [copy_recursive(v) for v in value]
        return result if len(result) > 0 else None
    elif isinstance(new_data, list):
        result = []
        for item in new_data:
            new_item = copy_recursive(item)
            if isinstance(new_item, list):
                result.extend(new_item)
            elif new_item is not None:
                result.append(new_item)
        return result
    else:
        return new_data


# -----------------------------------------------------------------------------
def architecture(cluster):
    arch_dict = {
        "balfrin": "gh200",
        "beverin": "mi300",
        "bristen": "gh200",
        "clariden": "gh200",
        "daint": "gh200",
        "eiger": "zen2",
        "oryx": "ada",
        "pilatus": "gh200",
        "santis": "gh200",
        "tasna": "gh200",
        "todi": "gh200",
    }
    try:
        return arch_dict[cluster]
    except KeyError:
        raise ValueError(
            f"Unknown cluster: {cluster}, please use one of {list(arch_dict.keys())}"
        )


# -----------------------------------------------------------------------------
def parse_arguments():
    script_path = os.path.dirname(os.path.abspath(__file__))
    template_path = script_path
    output_path = script_path
    if script_path.endswith("templates"):
        output_path = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(
        description="Generate a recipe with includes processed."
    )
    parser.add_argument(
        "-m",
        "--mpi",
        type=str,
        default="mpich",
        help="MPI flavour (mpich/ompi...) for YAML template name",
    )
    parser.add_argument(
        "-a",
        "--arch",
        type=str,
        help="Architecture (gh200, mc...) for YAML template name",
    )
    parser.add_argument(
        "-c",
        "--compiler",
        type=str,
        default="gcc",
        help="Compiler (gcc, llvm) for YAML template name",
    )
    parser.add_argument(
        "-C",
        "--cluster",
        type=str,
        default="daint",
        help="Cluster (daint/santis...) used for ${CLUSTER} substitution",
    )
    parser.add_argument(
        "-r",
        "--recipe",
        type=str,
        default="test",
        help="Recipe name",
    )
    parser.add_argument(
        "-v",
        "--variant",
        type=str,
        default="",
        help="Variant (e.g. osmesa) for ${VARIANT} substitution",
    )
    parser.add_argument(
        "-t", "--template", type=str, default=template_path, help="Template dir"
    )
    parser.add_argument(
        "-o", "--output", type=str, default=output_path, help="Output directory"
    )
    parser.add_argument(
        "-k",
        "--keyvals",
        type=str,
        default="",
        help="Comma separated key=value pairs for additional substitutions",
    )
    return parser.parse_args()


# -----------------------------------------------------------------------------
def banner(title):
    print()
    print("#" * 50)
    print(title)
    print("#" * 50)


# -----------------------------------------------------------------------------
def perform_file_substitution(name, input_file, output_file):
    # ------------------------------------------------
    banner(f"{name:15}, Text ${{VARIABLE}} substitutions")
    with open(input_file, "r") as file:
        content = file.readlines()
    content = [substitute_vars(line) for line in content]
    content = "".join(content)

    if not input_file.endswith(".yaml"):
        with open(output_file, "w") as file:
            file.write(content)

    else:
        # ------------------------------------------------
        # convert yaml string into yaml dict
        data = yaml.full_load(content)
        # print(yaml.dump(data))

        # ------------------------------------------------
        banner(f"{name:15}, Substitutions")
        generated_yaml = copy_recursive(data)

        # ------------------------------------------------
        banner(f"{name:15}, Generated YAML")
        print(yaml.dump(generated_yaml))

        # ------------------------------------------------
        # Write generated yaml to destination directory
        with open(output_file, "w") as file:
            yaml.dump(generated_yaml, file)


# -----------------------------------------------------------------------------
def main():
    global arch, compiler, mpi, envname, cluster, variant, recipe, generated_path
    #
    args = parse_arguments()
    mpi = args.mpi
    cluster = args.cluster
    arch = architecture(cluster)
    compiler = args.compiler
    recipe = args.recipe
    variant = args.variant
    out_path = os.path.abspath(args.output)
    template_path = os.path.abspath(args.template)
    output_path = os.path.join(out_path, arch)
    # put the $HOME dir in the path that is written to the file
    generated_path = output_path.replace(os.path.expanduser("~"), "$HOME")

    banner("Arguments/Variables")
    envname = f"{recipe}-{arch}-{mpi}-{compiler}".lower()
    # Capitalize the first letter of each component
    # envname2 = "".join([part.capitalize() for part in [recipe, arch, mpi, compiler]])
    print(f"envname         = {envname}")
    print(f"recipe          = {recipe}")
    print(f"arch            = {arch}")
    print(f"compiler        = {compiler}")
    print(f"mpi             = {mpi}")
    print(f"cluster         = {cluster}")
    print(f"variant         = {variant}")
    print(f"template_dir    = {template_path}")
    print(f"output_dir      = {output_path}")
    print(f"generated_dir   = {generated_path}")
    print(f"keyvals         = {args.keyvals}")

    # create output dir for arch
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    #
    template_filelist = {
        "cache-config.yaml": None,
        "compilers.yaml": None,
        "config.yaml": None,
        "environments.yaml": None,
        "modules.yaml": None,
        "packages.yaml": None,
        "post-install": None,
        "post-install-${ARCH}": "post-install",
        "job-build.sh": None,
        "job-build-${ARCH}.sh": "job-build.sh",
    }
    symlinks = [
        item for item in os.listdir(template_path)
        if os.path.islink(os.path.join(template_path, item))
    ]
    print("symlinks found", symlinks)

    for inname, outname in template_filelist.items():
        file_path = os.path.join(template_path, substitute_vars(inname))
        if os.path.exists(file_path):
            output_file_path = os.path.join(
                output_path, inname if outname is None else outname
            )
            perform_file_substitution(inname, file_path, output_file_path)

    for symlink in symlinks:
        symlink_dest = os.path.join(template_path, symlink)
        if os.path.exists(symlink_dest):
            output_symlink_path = os.path.join(output_path, symlink)
            if os.path.exists(output_symlink_path):
                print(f"Removing existing symlink {output_symlink_path}")
                os.remove(output_symlink_path)
            symlink_dest = os.path.relpath(
                symlink_dest, os.path.dirname(output_symlink_path)
            )
            os.symlink(
                symlink_dest,
                output_symlink_path,
                target_is_directory=os.path.isdir(symlink_dest),
            )
            print(f"Created symlink {output_symlink_path} -> {symlink_dest}")

    if args.arch is not None and arch != args.arch:
        banner(
            f"Warning: architecture {args.arch} is not supported on cluster {cluster}"
        )


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
