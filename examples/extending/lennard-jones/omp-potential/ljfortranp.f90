module ljfortranp

implicit none

private

public :: potential
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

end module ljfortranp
