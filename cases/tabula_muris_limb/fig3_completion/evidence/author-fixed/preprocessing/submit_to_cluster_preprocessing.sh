#!/bin/bash

#########################################################################################################
## Parameters for mxq-cluster job submission, change it according to your in-house server requirements.##
#########################################################################################################

THREADS=4
MEMORY=100G
MINUTES=120
TMPDIR=80G

datadir="./data/real"
indir="${datadir}/raw"
outdir="${datadir}/preprocessed"
logdir=${outdir}/log

SCRIPT="./preprocessing/data_preprocessing.R"

mkdir -p $outdir
mkdir -p $logdir

truth='truth'
pcts=0.01
ntop=NULL

suffix="_raw"

###############
# ZeiselBrain #
###############

file="${indir}/ZeiselBrain_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org mm \
  --mt

#################
# BaronPancreas #
#################

file="${indir}/BaronPancreas_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt

############
# Darmanis #
############

file="${indir}/Darmanis_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt

###############
# FreytagGold #
###############

file="${indir}/FreytagGold_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt


############
# PBMC_10X #
############

file="${indir}/PBMC_10X_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt

########################
# Tirosh_nonmaglignant #
########################

file="${indir}/Tirosh_nonmaglignant_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt


#########################
# tabula_sapiens_tissue #
#########################

file="${indir}/tabula_sapiens_tissue_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --mt

#########################
# dmel spatial E14-16h #
#########################

file="${indir}/dmel_E14-16h_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth $truth \
  --org hs \
  --rmbatch TRUE \
  --batchlab 'slice_ID' \
  --modpoisson FALSE \
  --mt

####################
# Tabula Muris All #
####################

name="tabula_muris"

file="${indir}/${name}_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth "cell_ontology_class" \
  --org mm \
  --mt

#####################
# Tabula Muris Limb #
#####################

name="tabula_muris_limb"

file="${indir}/${name}_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth "cell_ontology_class" \
  --org mm \
  --mt

###################
# Brain Organoids #
###################

BO_SCRIPT="./data_preprocessing_brain_organoids.R"

file="${indir}/brain_organoids_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$MEMORY \
  --tmpdir=$TMPDIR \
  -t $MINUTES \
Rscript-4.4 $BO_SCRIPT   \
       --outdir $outdir \
       --file $file \
       --name "${filename}_preproc" \
       --pct 0.01 \
       --truth "cell_type" \
       --org hs \
       --mt_perc 40 \
       --mt


#######################
# Tabula Sapiens full #
#######################

TS_MEMORY=500G
TS_MINUTES=360
name="tabula_sapiens"

file="${indir}/${name}_raw.rds"
filename=$(basename $file .rds)
filename=${filename%"$suffix"}

mxqsub \
  --stdout="${logdir}/${filename}_preproc-${pcts}.stdout.log" \
  --stderr="${logdir}/${filename}_preproc-${pcts}.stderr.log" \
  --group-name="${filename}" \
  --threads=$THREADS \
  --memory=$TS_MEMORY \
  --tmpdir=$TMPDIR \
  -t $TS_MINUTES \
  Rscript-4.4 $SCRIPT \
  --outdir $outdir \
  --file $file \
  --name "${filename}_preproc" \
  --pct $pcts \
  --truth "cell_ontology_class" \
  --org hs \
  --mt
