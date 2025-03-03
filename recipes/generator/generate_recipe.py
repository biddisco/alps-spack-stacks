import yaml
import yaml_include
import os
import sys
import argparse


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
def merge_sub_strings(data):
    strings = data.split("\n")
    result = []
    unindent = False
    for line in strings:
        if "- - " in line:
            unindent = True
            line = line.replace("- - ", "- ")
        elif "- " not in line:
            unindent = False
        elif unindent:
            line = line.replace("  - ", "- ")
        result.append(line)
    return "\n".join(result)


def architecture(cluster):
    arch_dict = {
        "balfrin": "gh200",
        "bristen": "gh200",
        "clariden": "gh200",
        "daint": "gh200",
        "eiger": "mc",
        "oryx": "turing",
        "pilatus": "gh200",
        "santis": "gh200",
        "tasna": "gh200",
        "todi": "gh200",
    }
    return arch_dict[cluster]


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
        help="Recipe name (<recipe>.yaml in template dir)",
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
    return parser.parse_args()


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

    # add custom tag for includes in yaml loader
    yaml.add_constructor("!inc", yaml_include.Constructor(base_dir=template_path))

    envname = f"{recipe}-{arch}-{compiler}-{mpi}"
    print("\n")
    print(f"arch={arch}")
    print(f"compiler={compiler}")
    print(f"mpi={mpi}")
    print(f"recipe={recipe}")
    print(f"envname={envname}")
    print(f"cluster={cluster}")
    print(f"variant={variant}")
    print(f"template_dir={template_path}")
    print(f"output_dir={output_path}")
    print(f"generated_dir={generated_path}")
    print("\n")
    #
    output_file = os.path.join(output_path, "environments.yaml")
    # create output dir for arch
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    #
    recipe_path = os.path.join(template_path, recipe + ".yaml")

    # ------------------------------------------------
    # load yaml as simple text and substitue all vars
    with open(recipe_path, "r") as file:
        content = file.readlines()
    content = [substitute_vars(line) for line in content]
    content = "".join(content)

    # ------------------------------------------------
    # load string as yaml with all !inc statements processed
    data = yaml.full_load(content)

    # ------------------------------------------------
    # dump yaml back to a string
    data_str = yaml.safe_dump(data, width=float("inf"))

    # ------------------------------------------------
    # merge keys that were suplicated (specs: for example)
    data_str = merge_sub_strings(data_str)
    print(data_str)

    # ------------------------------------------------
    # save the final yaml to the output file
    with open(output_file, "w") as file:
        file.write(data_str)

    #
    filelist = [
        "config.yaml",
        "cache-config.yaml",
        f"{compiler}-compilers.yaml",
        f"{arch}-packages.yaml",
        "post-install",
        f"{arch}-post-install",
        f"job-build.sh",
    ]
    for filename in filelist:
        file_path = os.path.join(template_path, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                content = file.readlines()
            content = [substitute_vars(line) for line in content]

            subst = [
                "bootstrap.yaml",
                "packages.yaml",
                "compilers.yaml",
                "post-install",
            ]
            for s in subst:
                if filename.endswith(s):
                    filename = s
            output_file_path = os.path.join(output_path, filename)
            with open(output_file_path, "w") as file:
                file.writelines(content)

    symlinks = ["repo"]
    for link in symlinks:
        link_path = os.path.join(template_path, link)
        if os.path.islink(link_path):
            target_path = os.readlink(link_path)
            output_symlink_path = os.path.join(output_path, link)
            if os.path.exists(output_symlink_path):
                print(f"Removing existing symlink {output_symlink_path}")
                os.remove(output_symlink_path)
            os.symlink(target_path, output_symlink_path, target_is_directory=True)
            print(f"Created symlink {output_symlink_path} -> {target_path}")

    if args.arch is not None and arch != args.arch:
        print(
            "*" * 50
            + "\n"
            + f"Warning: architecture {args.arch} is not supported on cluster {cluster}"
            + "\n"
            + "*" * 50
        )


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
