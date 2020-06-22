with import <nixpkgs> { config = { allowUnfree = true; }; };
let
  my-python-packages = python-packages:
    with python-packages; [
      pylint
      notebook
      pandas
      rope
    ];
  my-python = python37.withPackages my-python-packages;
in pkgs.mkShell {
  buildInputs = [
    pkgs.python37Packages.pip
    my-python
    pkgs.vscode # IDE
    pkgs.swig # dependency for: endesive
    pkgs.openssl.dev # dependency for: endesive
    pkgs.imagemagickBig # dependency for: wand
  ];
  shellHook = ''
    alias pip="PIP_PREFIX='$(pwd)/_build/pip_packages' \pip"
    export PYTHONPATH="$(pwd)/_build/pip_packages/lib/python3.7/site-packages:$PYTHONPATH" 
    unset SOURCE_DATE_EPOCH
  '';
  MAGICK_HOME = "${pkgs.imagemagickBig}";
}
