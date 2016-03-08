module ljfortran

implicit none

private

public :: potential, force, potential_and_force
public :: apply_pbc_dist

contains

function apply_pbc_dist(v, box, ibox, d) result(dist)
! Function to apply periodic boundaries to a given vector.
!
! Parameters
! ----------
! v : the distance vector to pbc-wrap
! box : the box lengths
! ibox : the inverse box lengths, ibox = 1.0 / box
! d : dimensionality of the vectors
!
! Returns
! -------
! dist : the pbc-wrapped distance vector
implicit none
integer, intent(in) :: d
double precision, dimension(d), intent(in) :: v, box, ibox
double precision, dimension(d) :: dist
integer :: i
dist = 0.0D0
do i=1,d
    dist(i) = v(i) - nint(v(i) * ibox(i)) * box(i)
end do
end function apply_pbc_dist

subroutine potential(pos, box, ibox, lj3, lj4, rcut2, offset, ptype, n, d, p, vpot) 
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
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box, ibox
double precision, dimension(p, p), intent(in) :: lj3, lj4, offset, rcut2
integer, dimension(n), intent(in) :: ptype
double precision, intent(out) :: vpot
double precision, dimension(d) :: posi, posj, rij
double precision :: rsq, r2inv, r6inv
integer :: i, j, itype, jtype
vpot = 0.0D0
do i=1,n-1
    posi = pos(i, :)
    itype = ptype(i) + 1
    do j=i+1,n
        posj = pos(j, :)
        jtype = ptype(j) + 1
        rij = apply_pbc_dist(posi - posj, box, ibox, d)
        rsq = dot_product(rij, rij)
        if (rsq < rcut2(itype, jtype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv**3
            vpot = vpot + r6inv * (lj3(itype, jtype) * r6inv - lj4(itype, jtype))
            vpot = vpot - offset(itype, jtype)
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
double precision, dimension(n, d), intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box, ibox
double precision, dimension(p, p), intent(in) :: lj1, lj2, rcut2
integer, dimension(n), intent(in) :: ptype
double precision, dimension(d) :: posi, posj, rij, forceij
double precision :: rsq, r2inv, r6inv, forcelj
integer :: i, j, itype, jtype
integer :: k, l
forces = 0.0D0
virial = 0.0D0
do i=1,n-1
    posi = pos(i, :)
    itype = ptype(i) + 1
    do j=i+1,n
        posj = pos(j, :)
        jtype = ptype(i) + 1
        rij = apply_pbc_dist(posi - posj, box, ibox, d)
        rsq = dot_product(rij, rij)
        if (rsq < rcut2(itype, jtype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv**3
            forcelj = r2inv * r6inv * (lj1(itype, jtype) * r6inv - lj2(itype, jtype))
            forceij = forcelj * rij
            forces(i,:) = forces(i,:) + forceij
            forces(j,:) = forces(j,:) - forceij
            ! accumulate for the virial:
            forall (k=1:d)
                forall(l=1:d)
                    virial(k,l) = virial(k,l) + forceij(k) * rij(l)
                end forall
            end forall
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
double precision, dimension(n, d), intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, intent(out) :: vpot
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box, ibox
double precision, dimension(p, p), intent(in) :: lj1, lj2, lj3, lj4, offset, rcut2
integer, dimension(n), intent(in) :: ptype
double precision, dimension(d) :: posi, posj, rij, forceij
double precision :: rsq, r2inv, r6inv, forcelj
integer :: i, j, itype, jtype
integer :: k, l
forces = 0.0D0
virial = 0.0D0
vpot = 0.0D0
do i=1,n-1
    posi = pos(i, :)
    itype = ptype(i) + 1
    do j=i+1,n
        posj = pos(j, :)
        jtype = ptype(j) + 1
        rij = apply_pbc_dist(posi - posj, box, ibox, d)
        rsq = dot_product(rij, rij)
        if (rsq < rcut2(itype, jtype)) then
            r2inv = 1.0D0 / rsq
            r6inv = r2inv**3
            forcelj = r2inv * r6inv * (lj1(itype, jtype) * r6inv - lj2(itype, jtype))
            forceij = forcelj * rij
            forces(i,:) = forces(i,:) + forceij
            forces(j,:) = forces(j,:) - forceij
            vpot = vpot + r6inv * (lj3(itype, jtype) * r6inv - lj4(itype, jtype))
            vpot = vpot - offset(itype, jtype)
            ! accumulate for the virial:
            forall (k=1:d)
                forall(l=1:d)
                    virial(k,l) = virial(k,l) + forceij(k) * rij(l)
                end forall
            end forall
        end if
    end do
end do
end subroutine potential_and_force

end module ljfortran
