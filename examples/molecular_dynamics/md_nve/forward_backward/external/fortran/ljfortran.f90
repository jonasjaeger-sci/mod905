! Copyright (c) 2021, PyRETIS Development Team.
! Distributed under the LGPLv2.1+ License. See LICENSE for more info.
module ljfortran

implicit none

private

public :: potential, force, potential_and_force
public :: pbc_dist

contains

function pbc_dist(v, box, ibox) result(dist)
! Function to apply periodic boundaries to a given displacement.
!
! Parameters
! ----------
! v : the displacement to pbc-wrap
! box : the box lengths
! ibox : the inverse box lengths, ibox = 1.0 / box
!
! Returns
! -------
! dist : the pbc-wrapped displacement
implicit none
double precision :: dist
double precision, intent(in) :: v, box, ibox
dist = v - nint(v * ibox) * box
end function pbc_dist

subroutine potential(pos, box, ibox, lj3, lj4, offset, rcut2, ptype, n, d, p, vpot)
! Function to evaluate the Lennard-Jones potential
!
! Parameters
! ----------
! pos : positions of the particles
! box : the box lengths
! ibox : the inverse box lengths, ibox = 1.0 / box
! lj3 : Lennard-Jones parameters, 4.0 * epsilonij * sigmaij**12
! lj4 : Lennard-Jones parameters, 4.0 * epsilonij * sigmaij**6
! rcut2 : Squared cut-offs
! offset : Potential energy shift
! ptype : identifier for the particle types
! n : number of particles
! d : dimensionality of the vectors
! p : number of particle types
!
! Returns
! -------
! vpot : the potential energy
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), target, intent(in) :: pos
double precision, dimension(d), intent(in) :: box, ibox
double precision, dimension(p, p), intent(in) :: lj3, lj4, offset, rcut2
integer, dimension(n), intent(in) :: ptype
double precision, intent(out) :: vpot
double precision :: rsq, r2inv, r6inv, dx, dy, dz
double precision, dimension(:), pointer :: x, y, z
integer :: i, j, itype, jtype
vpot = 0.0D0
x => pos(1:n,1)
y => pos(1:n,2)
z => pos(1:n,3)
do i=1,n-1
    itype = ptype(i) + 1
    do j=i+1,n
        jtype = ptype(j) + 1
        dx = x(i) - x(j)
        dy = y(i) - y(j)
        dz = z(i) - z(j)
        dx = pbc_dist(dx, box(1), ibox(1)) 
        dy = pbc_dist(dy, box(2), ibox(2)) 
        dz = pbc_dist(dz, box(3), ibox(3)) 
        rsq = dx*dx + dy*dy + dz*dz
        if (rsq < rcut2(jtype, itype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv**3
            vpot = vpot + r6inv * (lj3(jtype, itype) * r6inv - lj4(jtype, itype))
            vpot = vpot - offset(jtype, itype)
        end if
    end do
end do
end subroutine potential

subroutine force(pos, box, ibox, lj1, lj2, rcut2, ptype, n, d, p, forces, virial)
! Function to evaluate the Lennard-Jones force
!
! Parameters
! ----------
! pos : positions of the particles
! box : the box lengths
! ibox : the inverse box lengths, ibox = 1.0 / box
! lj1 : Lennard-Jones parameters, 48.0 * epsilonij * sigmaij**12
! lj2 : Lennard-Jones parameters, 24.0 * epsilonij * sigmaij**6
! rcut2 : Squared cut-offs
! ptype : identifier for the particle types
! n : number of particles
! d : dimensionality of the vectors
! p : number of particle types
!
! Returns
! -------
! forces : the Lennard-Jones forces on the particles
! virial : the virial matrix
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), target, intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, dimension(n, d), target, intent(in) :: pos
double precision, dimension(d), intent(in) :: box, ibox
double precision, dimension(p, p), intent(in) :: lj1, lj2, rcut2
integer, dimension(n), intent(in) :: ptype
double precision, dimension(:), pointer :: x, y, z, fx, fy, fz
double precision :: rsq, r2inv, r6inv, forcelj, dx, dy, dz
double precision :: forceij_x, forceij_y, forceij_z
integer :: i, j, itype, jtype
x => pos(1:n, 1)
y => pos(1:n,2)
z => pos(1:n,3)
fx => forces(1:n,1)
fy => forces(1:n,2)
fz => forces(1:n,3)
forces = 0.0D0
virial = 0.0D0
do i=1,n-1
    itype = ptype(i) + 1
    do j=i+1,n
        jtype = ptype(j) + 1
        dx = x(i) - x(j)
        dy = y(i) - y(j)
        dz = z(i) - z(j)
        dx = pbc_dist(dx, box(1), ibox(1)) 
        dy = pbc_dist(dy, box(2), ibox(2)) 
        dz = pbc_dist(dz, box(3), ibox(3)) 
        rsq = dx*dx + dy*dy + dz*dz
        if (rsq < rcut2(jtype, itype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv*r2inv*r2inv
            forcelj = r2inv * r6inv * (lj1(jtype, itype) * r6inv - lj2(jtype, itype))
            forceij_x = forcelj * dx
            forceij_y = forcelj * dy
            forceij_z = forcelj * dz
            fx(i) = fx(i) + forceij_x
            fy(i) = fy(i) + forceij_y
            fz(i) = fz(i) + forceij_z
            fx(j) = fx(j) - forceij_x
            fy(j) = fy(j) - forceij_y
            fz(j) = fz(j) - forceij_z
            ! accumulate for the virial:
            virial(1,1) = virial(1,1) + forceij_x * dx
            virial(1,2) = virial(1,2) + forceij_x * dy
            virial(1,3) = virial(1,3) + forceij_x * dz
            virial(2,1) = virial(2,1) + forceij_y * dx
            virial(2,2) = virial(2,2) + forceij_y * dy
            virial(2,3) = virial(2,3) + forceij_y * dz
            virial(3,1) = virial(3,1) + forceij_z * dx
            virial(3,2) = virial(3,2) + forceij_z * dy
            virial(3,3) = virial(3,3) + forceij_z * dz
        end if
    end do
end do
end subroutine force

subroutine potential_and_force(pos, box, ibox, lj1, lj2, lj3, lj4, offset, rcut2, ptype, n, d, p, forces, virial, vpot) 
! Function to evaluate the Lennard-Jones force and potential
!
! Parameters
! ----------
! pos : positions of the particles
! box : the box lengths
! ibox : the inverse box lengths, ibox = 1.0 / box
! lj1 : Lennard-Jones parameters, 48.0 * epsilonij * sigmaij**12
! lj2 : Lennard-Jones parameters, 24.0 * epsilonij * sigmaij**6
! lj3 : Lennard-Jones parameters, 4.0 * epsilonij * sigmaij**12
! lj4 : Lennard-Jones parameters, 4.0 * epsilonij * sigmaij**6
! rcut2 : Squared cut-offs
! offset : Potential energy shift
! ptype : identifier for the particle types
! n : number of particles
! d : dimensionality of the vectors
! p : number of particle types
!
! Returns
! -------
! vpot : the potential energy
! forces : the Lennard-Jones forces on the particles
! virial : the virial matrix
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), target, intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, intent(out) :: vpot
double precision, dimension(n, d), target, intent(in) :: pos
double precision, dimension(d), intent(in) :: ibox, box
double precision, dimension(p, p), intent(in) :: lj1, lj2, lj3, lj4, offset, rcut2
double precision, dimension(:), pointer :: x, y, z, fx, fy, fz
integer, dimension(n), intent(in) :: ptype
double precision :: rsq, r2inv, r6inv, forcelj, dx, dy, dz
double precision :: forceij_x, forceij_y, forceij_z
integer :: i, j, itype, jtype
forces = 0.0D0
virial = 0.0D0
vpot = 0.0D0
x => pos(1:n,1)
y => pos(1:n,2)
z => pos(1:n,3)
fx => forces(1:n,1)
fy => forces(1:n,2)
fz => forces(1:n,3)
do i=1,n-1
    itype = ptype(i) + 1
    do j=i+1,n
        jtype = ptype(j) + 1
        dx = x(i) - x(j)
        dy = y(i) - y(j)
        dz = z(i) - z(j)
        dx = pbc_dist(dx, box(1), ibox(1)) 
        dy = pbc_dist(dy, box(2), ibox(2)) 
        dz = pbc_dist(dz, box(3), ibox(3)) 
        rsq = dx*dx + dy*dy + dz*dz
        if (rsq < rcut2(jtype, itype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv*r2inv*r2inv
            forcelj = r2inv * r6inv * (lj1(jtype, itype) * r6inv - lj2(jtype, itype))
            forceij_x = forcelj * dx
            forceij_y = forcelj * dy
            forceij_z = forcelj * dz
            fx(i) = fx(i) + forceij_x
            fy(i) = fy(i) + forceij_y
            fz(i) = fz(i) + forceij_z
            fx(j) = fx(j) - forceij_x
            fy(j) = fy(j) - forceij_y
            fz(j) = fz(j) - forceij_z
            vpot = vpot + r6inv * (lj3(jtype, itype) * r6inv - lj4(jtype, itype))
            vpot = vpot - offset(jtype, itype)
            ! accumulate for the virial:
            virial(1,1) = virial(1,1) + forceij_x * dx
            virial(1,2) = virial(1,2) + forceij_x * dy
            virial(1,3) = virial(1,3) + forceij_x * dz
            virial(2,1) = virial(2,1) + forceij_y * dx
            virial(2,2) = virial(2,2) + forceij_y * dy
            virial(2,3) = virial(2,3) + forceij_y * dz
            virial(3,1) = virial(3,1) + forceij_z * dx
            virial(3,2) = virial(3,2) + forceij_z * dy
            virial(3,3) = virial(3,3) + forceij_z * dz
        end if
    end do
end do
end subroutine potential_and_force

end module ljfortran
