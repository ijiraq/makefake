      real (kind=8) FUNCTION ran3(idum)
      implicit none
      
      integer, intent(inout) :: idum
      integer, parameter :: MBIG=1000000000, MSEED=161803398, MZ=0
      real (kind=8), parameter :: FAC=1.d0/MBIG
      integer, save :: iff, inext, inextp, ma(55)
      integer :: i, ii, mj, mk, k
      
      data iff /0/
      
      if(idum.lt.0.or.iff.eq.0)then
         iff=1
         mj=abs(MSEED-abs(idum))
         mj=mod(mj,MBIG)
         ma(55)=mj
         mk=1
         do i=1,54
            ii=mod(21*i,55)
            ma(ii)=mk
            mk=mj-mk
            if(mk.lt.MZ)mk=mk+MBIG
            mj=ma(ii)
         end do
         do k=1,4
            do i=1,55
               ma(i)=ma(i)-ma(1+mod(i+30,55))
               if(ma(i).lt.MZ)ma(i)=ma(i)+MBIG
            end do
         end do
         inext=0
         inextp=31
         idum=1
      endif
      inext=inext+1
      if(inext.eq.56)inext=1
      inextp=inextp+1
      if(inextp.eq.56)inextp=1
      mj=ma(inext)-ma(inextp)
      if(mj.lt.MZ)mj=mj+MBIG
      ma(inext)=mj
      ran3=mj*FAC
      return
      end function ran3
      
