! Copyright (c) 2023, PyRETIS Development Team.
! Distributed under the LGPLv2.1+ License. See LICENSE for more info.
module ordermod

implicit none

private

public :: calculate

contains

subroutine calculate(pos, n, d, orderp) 
! Subroutine to evaluate the potential
implicit none
integer, intent(in) :: n, d
double precision, dimension(n, d), intent(in) :: pos
double precision, intent(out) :: orderp
integer, dimension(6) :: temp1
integer, dimension(24) :: temp2
double precision, dimension(3) :: cm1, cm2, cmvec, molvec
double precision :: resl
integer :: i

temp1(:) = (/56,64,104,112,200,208/)
temp2(:) = (/56, 64, 72, 80,104,112,136,152,168,176,200,208,232,&
             248,264,272,296,304,328,336,344,352,360,368/)

cm1(:) = 0.d0
cm2(:) = 0.d0
resl = 1000.d0
do i=1,6
    cm1(:)=cm1(:)+nint(pos(temp1(i)*4-3,:)*resl)/resl 
end do    
do i=1,24 
    cm2(:)=cm2(:)+nint(pos(temp2(i)*4-3,:)*resl)/resl 
end do   
cm1(:) = cm1(:) / 6.d0
cm2(:) = cm2(:) / 24.d0
cmvec = cm2(:) - cm1(:)
molvec= nint(pos(368*4+1,:)*resl)/resl - cm1(:)
       
orderp=-sum(cmvec(:)*molvec(:))/sqrt(sum(cmvec(:)*cmvec(:)))
end subroutine calculate

end module ordermod
