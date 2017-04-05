! Copyright (c) 2015, PyRETIS Development Team.
! Distributed under the LGPLv3 License. See LICENSE for more info.
module vvintegrator

implicit none

private

public :: rangaussian, gssbivar, seed_random_generator, get_seed_size
public :: overdamped, inertia1, inertia2

contains

function get_seed_size() result(n)
! implicit none
integer :: n
call random_seed(size=n)
end function get_seed_size

subroutine seed_random_generator(seed, n)
! Seed the random generator for fortran
implicit none
integer, intent(in) :: n
integer, dimension(n), intent(in) :: seed
call random_seed(put=seed)
end subroutine seed_random_generator

function rangaussian(sigma) result(rng)
! Generate random number from Gaussian distribution
implicit none
double precision :: rng
double precision, intent(in) :: sigma
double precision :: s, gx, gy, r

s = 2.
do while (s > 1.)
  call random_number(gx)
  call random_number(gy)
  gx = 2.0 * gx - 1.0
  gy = 2.0 * gy - 1.0
  s = gx**2 + gy**2
end do
r = -2.0 * log(s) / s
rng = sigma * gx * sqrt(r)
end function rangaussian

subroutine gssbivar(s12os11, sqrts11, sqrtSos11, rdr, rdv)
! Draw from gaussian bivariate
implicit none
double precision, intent(in) :: s12os11, sqrts11, sqrtSos11
double precision, intent(out) :: rdr, rdv
double precision :: s, gx, gy, r

s = 2.0
do while (s > 1.)
  call random_number(gx)
  call random_number(gy)
  gx = 2.0 * gx - 1.0
  gy = 2.0 * gy - 1.0
  s = gx**2 + gy**2
end do
r = sqrt(-2.0 * log(s) / s)
rdr = gx * r * sqrts11
rdv = gy * r * sqrtSos11 + rdr*s12os11
end subroutine gssbivar

subroutine overdamped(pos, vel, force, bddt, sigma, n, d, posn, veln)
! Do overdamped langevin
implicit none
integer, intent(in) :: n, d
double precision, dimension(n), intent(in) :: bddt, sigma
double precision, dimension(n, d), intent(in) :: pos, vel, force
double precision, dimension(n, d), intent(out) :: posn, veln
double precision, dimension(n) :: rnd
integer :: i

do i = 1, n
  rnd(i) = rangaussian(sigma(i))
end do

do i = 1, d
   posn(:,i) = pos(:,i) + bddt(:)*force(:,i) + rnd(i)
   veln(:,i) = rnd(i)
end do
end subroutine overdamped


subroutine inertia1(pos, vel, force, gammav, c_0, a_1, a_2, b_1, s12os11, sqrts11, sqrtsos11, n, d, posn, veln)
! Do underdamped langevin
implicit none
integer, intent(in) :: n, d
double precision, intent(in) :: gammav, c_0, a_1
double precision, dimension(n), intent(in) :: s12os11, sqrts11, sqrtsos11, a_2, b_1
double precision, dimension(n, d), intent(in) :: pos, vel, force
double precision, dimension(n, d), intent(out) :: posn, veln
double precision :: randx, randv
integer :: i, j

do j = 1, d
  do i = 1, n
    if (gammav > 0) then
       call gssbivar(s12os11(i), sqrts11(i), sqrtsos11(i), randx, randv)
    else
        randx = 0.0
        randv = 0.0
    end if
    posn(i,j) = pos(i,j) + a_1 * vel(i,j) + a_2(i) * force(i,j) + randx
    veln(i,j) = c_0 * vel(i,j) + b_1(i)*force(i,j) + randv
  end do
end do

end subroutine inertia1

subroutine inertia2(vel, force, b_2, n, d, veln)
! Do underdamped langevin, part2: update velocities
implicit none
integer, intent(in) :: n, d
double precision, dimension(n, d), intent(in) :: vel, force
double precision, dimension(n), intent(in) :: b_2
double precision, dimension(n, d), intent(out) :: veln
integer :: i

do i = 1, d
  veln(:,i) = vel(:,i) + b_2(:)*force(:,i)
end do
end subroutine inertia2
end module vvintegrator
