! Copyright (c) 2015, PyRETIS Development Team.
! Distributed under the LGPLv2.1+ License. See LICENSE for more info.
module vvintegrator

implicit none

private

public :: step1, step2

contains

subroutine step1(pos, vel, force, imass, delta_t, half_delta_t, n, d, dpos, dvel) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d
double precision, dimension(n, d), intent(in) :: pos, vel, force
double precision, dimension(n), intent(in) :: imass
double precision, intent(in) :: delta_t, half_delta_t
double precision, dimension(n, d), intent(out) :: dvel, dpos
integer :: i
dvel = 0.0D0
dpos = 0.0D0
do i=1,d
    dvel(:,i) = vel(:,i) + half_delta_t * force(:,i) * imass(:)
    dpos(:,i) = pos(:,i) + delta_t * dvel(:,i)
end do
end subroutine step1

subroutine step2(vel, force, imass, half_delta_t, n, d, dvel) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d
double precision, dimension(n, d), intent(in) :: vel, force
double precision, dimension(n), intent(in) :: imass
double precision, intent(in) :: half_delta_t
double precision, dimension(n, d), intent(out) :: dvel
integer :: i
dvel = 0.0D0
do i=1,d
    dvel(:,i) = vel(:,i) + half_delta_t * force(:,i) * imass(:)
end do
end subroutine step2

end module vvintegrator
