# rsync -av --exclude='.git' ./. ../testKubeOperator
# rsync -av --exclude='path1/to/exclude' --exclude='path2/to/exclude' source destination
rsync -av --exclude='.git'  --exclude='.github' ./. ../../git/qudoor/oneqloud/ui

