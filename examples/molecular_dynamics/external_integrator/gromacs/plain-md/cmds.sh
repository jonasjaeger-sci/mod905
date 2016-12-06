GMX=gmx_5.1.4
$GMX grompp -c initial.g96
$GMX mdrun -v -c confout.g96
echo 0 | $GMX trjconv -f traj.trr -o frame.g96 -sep -nzero 5 -s topol.tpr
mkdir -p frames
mv frame*.g96 frames
echo 1 2 3 4 5 6 7 8 | $GMX energy
