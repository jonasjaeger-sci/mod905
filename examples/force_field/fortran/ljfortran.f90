module ljfortran

implicit none

private

public :: potential, force, potential_and_force
public :: apply_pbc_dist

contains

function apply_pbc_dist(v, box, d)
  ! function to apply periodic boundaries to 
  ! a given vector
  implicit none
  integer, intent(in) :: d
  double precision, dimension(d) :: apply_pbc_dist
  double precision, dimension(d), intent(in) :: v, box
  double precision :: half_boxl, box_length
  integer :: i
  apply_pbc_dist = 0.0D0
  do i=1,d
    box_length = box(i)
    half_boxl = box_length * 0.5D0
    apply_pbc_dist(i) = v(i)
    do while (apply_pbc_dist(i) > half_boxl)
        apply_pbc_dist(i) = apply_pbc_dist(i) - box_length
    end do
    do while (apply_pbc_dist(i) < -half_boxl)
        apply_pbc_dist(i) = apply_pbc_dist(i) + box_length
    end do
  end do
end function apply_pbc_dist

subroutine potential(pos, box, lj3, lj4, rcut2, offset, ptype, n, d, p, vpot) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box
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
        rij = apply_pbc_dist(posi - posj, box, d)
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

subroutine force(pos, box, lj1, lj2, rcut2, ptype, n, d, p, forces, virial) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box
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
        rij = apply_pbc_dist(posi - posj, box, d)
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

subroutine potential_and_force(pos, box, lj1, lj2, lj3, lj4, offset, rcut2, ptype, n, d, p, forces, virial, vpot) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d, p
double precision, dimension(n, d), intent(out) :: forces
double precision, dimension(d, d), intent(out) :: virial
double precision, intent(out) :: vpot
double precision, dimension(n, d), intent(in) :: pos
double precision, dimension(d), intent(in) :: box
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
        rij = apply_pbc_dist(posi - posj, box, d)
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
