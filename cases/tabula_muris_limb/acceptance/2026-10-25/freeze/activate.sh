export CADIR_ENV=/workspace/cadir-env
export MAMBA_ROOT_PREFIX="$CADIR_ENV/mamba"
export CONDA_PKGS_DIRS="$CADIR_ENV/mamba/pkgs"
export XDG_CACHE_HOME="$CADIR_ENV/cache"
export PATH="$CADIR_ENV/skeleton_runtime/bin:$CADIR_ENV/bin:$PATH"
export R_LIBS_USER="$CADIR_ENV/R-library"
export RETICULATE_AUTOCONFIGURE=FALSE
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export MAKEFLAGS=-j2
export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
mkdir -p "$R_LIBS_USER" "$XDG_CACHE_HOME"
