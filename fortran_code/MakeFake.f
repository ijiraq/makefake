C-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
      include 'ran3.f'
      
      program XX

      implicit none

      integer(kind=4) obs_code, ierr, niter, nobjects, object_number
      integer(kind=4) output_lun, max_objects, max_iters
      integer(kind=4) field_number, i, j, version, k, seed


      real(kind=8) Pi, TwoPi, drad, mu, theta, phi, gi
      real(kind=8) gb, alpha, MA, ran3
      real(kind=8) a_limits(2), e_limits(2), i_limits(2)
      real(kind=8) h_limits(2), m_limits(2)
      real(kind=8) group


      parameter (Pi = 3.141592653589793238_8, TwoPi = 2.0d0*Pi,
     $     drad = Pi/180.0d0, mu = TwoPi**2)
      parameter (gb = 0.15, version=5)
      
      real(kind=8) obs_jday, fake_jday
      real(kind=8) a, e, inc, node, peri, M, H, pos(6), obs_pos(3)
      real(kind=8) vel(3)
      real(kind=8) epoch_M
      real(kind=8) ros, fake_obs_pos(3), fake_ros, dec_cen
      real(kind=8) ra, dec, delta, radius, mag, ddec, dra, ra_cen
      real(kind=8) fake_ra, fake_dec, fake_delta, fake_mag, fake_M
      real(kind=8) fake_ra2, fake_dec2, fake_delta2, fake_mag2, fake_M2
      real(kind=8) fake_obs_pos2(3), fake_ros2
      real(kind=8) obs_ra, obs_dec, obs_radius, cos_obs_dec
      real(kind=8) r, ran_mag
      character in_str*120
      character output_filename*120, field*120
      character*80 message

      max_iters = 1E9
      obs_code = 500

      CALL parse_args(field, ra_cen, dec_cen, obs_jday, 
     $                fake_jday, max_objects)

C     field == name of field to make fakes for, can be any string
C     ra_cen == central RA of region to get fake sources for (deg)
C     dec_cen == central DEC of region to get fake sources for (deg)
C     obs_jday == julian date that is the opposition date for this field centre
C     fkae_jday == date to generate source positions for
C     max_objects = number of objects to generate for this field.
      
      epoch_M = obs_jday

C     set the random seed to the same value for all runs, this is a
C     realization of the Kuiper belt
      seed=-123456789
      r=ran3(seed)


C     compute the cos_of_dec once as we need this many times.
      cos_obs_dec = cos(dec_cen*drad)

C     For each field we pull all the sources that are within 1.2
C     degrees. This ensures we can plant sources in every ccd of mosaic.
      obs_radius = 1.2*drad

C     create the output file name string, little finiky. 
      do i = 1, len(in_str)
         in_str(i:i) = ' '
         output_filename(i:i) = ' '
      end do

      write(in_str, 7002) "PlantList",field,
     $        ra_cen,dec_cen,fake_jday,".txt"
 7002 format (2(a10,"_"),3(f15.4,"_"),a4)

      j = 1
      do i = 1, len(in_str) 
         if (in_str(i:i) .ne. ' ') then
            output_filename(j:j) = in_str(i:i)
            j = j+1
         endif
      end do
      output_filename = trim(output_filename)
      write(6,*) "Writing to "//output_filename

      output_lun = 11
      open (unit=output_lun, file=output_filename, status='new')

C     Get observatory location for primary location
      call ObsPos (obs_code, obs_jday, obs_pos, 
     $     vel, ros, ierr)

C     Get the observer location at this fake date.
      call ObsPos (obs_code, fake_jday, fake_obs_pos,
     $     vel, fake_ros, ierr)

C     Get the observer location at fake date + 1 day (for rates)
      call ObsPos (obs_code, fake_jday+1, fake_obs_pos2,
     $     vel, fake_ros2, ierr)

      write(output_lun, 9002) ClassyMakeFakeV5.f'obj_id', 'RA', 'DEC', 'Delta',
     $     'mag', 'a', 
     $     'e', 'inc',
     $     'node', 'peri', 'M', 'H', 'dra_arc',
     $     'ddec_arc', 'r_sun', 'gi'

C     Loop over making fake objects until we have max_objects in frame
      niter = 1
      nobjects = 1
      do while ((nobjects .le. max_objects) .and. 
     $     (niter .lt. max_iters))
         
         a_limits = (/30.0_8,220.0_8/)
         e_limits = (/0.0_8,0.999_8/)
         i_limits = (/0.0_8,Pi/2.0/)
         m_limits = (/22.0_8,28.0_8/)
         group = ran3(seed)
         if (group .lt. 0.8 .and. group .gt. 0.5) then
             m_limits = (/25.5_8,27.5_8/)
         end if
         if (group .lt. 0.5) then
C            Classical belt object                 
             a_limits = (/40.0_8,50.0_8/)
             e_limits = (/0.0_8,0.5_8/)
             i_limits = (/0.0_8,Pi/6.0_8/)
         end if
         if (group .lt. 0.3) then
             m_limits = (/25.5_8,27.5_8/)
         end if

         niter = niter + 1
         a = a_limits(1) + ran3(seed)*(a_limits(2)-a_limits(1))
         e = e_limits(1) + ran3(seed)*(e_limits(2)-e_limits(1))
         inc = i_limits(1) + ran3(seed)*(i_limits(2)-i_limits(1))
         ran_mag = m_limits(1) + ran3(seed)*(m_limits(2)-m_limits(1))
         node = TwoPi*ran3(seed)
         peri = TwoPi*ran3(seed)
         M = TwoPi*ran3(seed)
C     compute a g-i color as randomly distributed between 0.5 and 1.5
C     color range in based of Oflek 2012 (SDDS colors of TNOS)
         gi = ran3(seed) + 0.5
            
            
         call pos_cart(a, e, inc, node, peri, M, pos(1),
     $        pos(2), pos(3))
         call RADECeclXV (pos, obs_pos, delta, ra, dec, ierr)
C     Given this random orbit determine if its on the image.

C     This loop selects sources that are within RADIUS for a field 
         obs_ra = ra_cen*drad
         obs_dec = dec_cen*drad
         if (radius(ra, dec, obs_ra, obs_dec) .lt. obs_radius) then
            nobjects = nobjects +1

C     Compute the Ground Based magnitude
            r = sqrt(pos(1)**2 + pos(2)**2 + pos(3)**2)
C     Set H based on randomize value of mag
            H = ran_mag -5*LOG10(r) - 5*LOG10(delta)

C     This orbit / object is inside our sample. 
C     Compute circumstances at current observation.

            fake_M = MA(M, epoch_M, a, fake_jday)
            call pos_cart(a, e, inc, node, peri, fake_M, pos(1),
     $           pos(2), pos(3))
            call RADECeclXV (pos, fake_obs_pos, fake_delta, 
     $           fake_ra, fake_dec, ierr)
            r = sqrt(pos(1)**2 + pos(2)**2 + pos(3)**2)
            call AppMag(r, delta, fake_ros, H, gb, alpha, 
     $           mag, ierr) 

C     Compute position 1 day later to get sky motion rate
            fake_M = MA(M, epoch_M, a, fake_jday+1.0)
            call pos_cart(a, e, inc, node, peri, fake_M, pos(1),
     $           pos(2), pos(3))

            call RADECeclXV (pos, fake_obs_pos2, fake_delta2, 
     $           fake_ra2, fake_dec2, ierr)

C     account for the fact we're doing this wrong. 
            dra = fake_ra2 - fake_ra
            if ( abs(dra) .gt. 1) then
               delta = TwoPi
               if ( dra .gt. 1 ) then
                  delta = -1*delta
               end if
               dra = dra + delta
            end if
            dra = dra*cos(fake_dec2)/24.0
            ddec = (fake_dec2-fake_dec)/24.0
            object_number = niter


            write (output_lun, 9001) object_number,
     $           fake_ra/drad, fake_dec/drad, fake_delta, mag,
     $           a, e, inc/drad, node/drad, peri/drad,
     $           fake_M/drad, H, 3600*dra/drad, 3600.0*ddec/drad,
     $           r, gi
            call flush(output_lun)
         end if
      end do

      STOP

 9001 format (i10, 15(f16.6,1x))
 9002 format (a10, 15(a16,1x))

      end program xx

      real*8 function radius(ra1, dec1, ra2, dec2)
      real*8 ra1, dec1, ra2, dec2
      
      radius = acos(sin(dec1)*sin(dec2) + 
     $     cos(dec1)*cos(dec2)*cos(ra1-ra2))
      return
      end function radius

      real*8 function MA(M, epoch_M, a, jday)
C     Move the Mean Annomally from jday to epoch_M

      real*8 M
      real*8 jday
      real*8 nu, TwoPi, epoch_M, a
      parameter (TwoPi=3.141592653589793238d0*2d0, nu=TwoPi/365.25d0)

      MA = M + (jday-epoch_M)*((nu/a**1.5))
      MA = MA - int(MA/TwoPi)*TwoPi
      return
      end function MA
      


      subroutine usage(message, ierr)
      character*80 message
      integer*4 ierr

      write(0,*) trim(message)
      write(0,*) ""

      write(0,*) "Usage: ClassyMakeFake FIELD RA DEC JD NITER"
      write(0,*) " FIELD -- Name of the field"
      write(0,*) " RA    -- RA of field center, in degrees"
      write(0,*) " DEC   -- RA of field center, in degrees"
      write(0,*) " JD    -- Julian Date assocaited to RA/DEC position"
      write(0,*) " JD    -- Julian Date for image to plant into"
      write(0,*) " NITER -- Number of KBOs to generate"
      write(0,*) ""

      call exit(ierr)
      end subroutine usage


      subroutine parse_args(name, ra, dec, obs_jd, fake_jd, max_objects)

C     Get the JD we will generate FAKE objects positions for.
C     Usage;  MakeFake obs_ra obs_dec obs_jday fake_jday number

      real*8 ra, dec, obs_jd, fake_jd
      character*80 message, command
      character*120 in_str, name
      integer*4 length
      integer*4 max_objects
      integer*4 nargs
      integer*4 argn


      nargs = COMMAND_ARGUMENT_COUNT()
      message = 'Wrong number of arguments'
      if (nargs .ne. 6) CALL usage(message, -1)

      argn = 0
      length = 80
      CALL GET_COMMAND_ARGUMENT(argn, command, length, ierr)
      if ( ierr .ne. 0 ) GOTO 1000

      argn = 1
      length = 120
      CALL GET_COMMAND_ARGUMENT(argn, name, length, ierr)
      if ( ierr .ne. 0 ) GOTO 1000

      argn = 2
      length = 80
      CALL GET_COMMAND_ARGUMENT(argn, in_str, length, ierr)
      if ( ierr .ne. 0 ) GOTO 1000
      read (in_str, *, err=1000) ra

      argn = 3
      CALL GET_COMMAND_ARGUMENT(argn, in_str, length, ierr)
      if (ierr .ne. 0) GOTO 1000
      read (in_str, *, err=1000) dec

      argn = 4
      CALL GET_COMMAND_ARGUMENT(argn, in_str, length, ierr)
      if (ierr .ne. 0) GOTO 1000
      read (in_str, *, err=1000) obs_jd

      argn = 5
      CALL GET_COMMAND_ARGUMENT(argn, in_str, length, ierr)
      if (ierr .ne. 0) GOTO 1000
      read (in_str, *, err=1000) fake_jd

C     Get the number of objects to generate
      argn = 6
      CALL GET_COMMAND_ARGUMENT(argn, in_str, length, ierr)
      if (ierr .ne. 0) GOTO 1000
      read (in_str, *, err=1000) max_objects

      write(0,*) "Executing command: ",command
      write(0,*) "Field Centre", ra, dec
      write(0,*) "Taken on JD:", obs_jd
      write(0,*) "Propogating elements to:", fake_jd
      write(0,*) "Number of objects:", max_objects
      RETURN

 1000 CONTINUE

      write(message, 1001) "Error parsing argument", argn
      message = trim(message)
      CALL usage(message, -1)
 1001 FORMAT('A20,I10')
      end subroutine parse_args

