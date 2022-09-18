c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
c 
c This program compute the position of objects at different times.
c Should be used once basic detectabilty is determined, ie this uses the 
c output of NHDetectability.
c
c This code add 0.7 to the lorri_mag values as Detectability didn't 
c covert to V from H_r. 
c
c Usage: Obj_at_Date model trajectory obs-date
c
c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
      
      include 'SurveySubs.f'

      program XX

      implicit none

      integer*4 n_obj_max, screen, keybd, verbose, lun_h, lun_t
      integer*4 code
      integer*4 nw_max, nw

      parameter
     $     (n_obj_max = 10000, screen = 6, keybd = 5, verbose = 9,
     $     nw_max = 30)

      integer*4 lw(nw_max)

      real*8 Pi, TwoPi, drad

      parameter (Pi = 3.141592653589793238d0, TwoPi = 2.0d0*Pi,
     $     drad = Pi/180.0d0)

      character*20 extra(nw_max)

c color array NEEDS to be length 10 or more!
      real*8 a, e, inc, node, peri, M, h, epoch,
     $     r, delta, ra, dec, random, mt, gb, ph, period, 
     $     amp, lorri_mag, q, 
     $     jday, m_rand, eff, rn_iter, eff_lim, h_rand, pos(3), 
     $     obpos(3),
     $     ros, tmp(3), obs_jday, jday_start, jday_step, jday_end, 
     $     mag,  ground_mag, ground_delta, alpha, eos, epos(3)

      integer*4 n_hits, n_track, ierr, seed, flag, isur, ic, n_iter,
     $  n_track_max, nchar, rierr, co, j, ext_index, start_idx, end_idx

      character distri_file*80, survey_dir*100, line*200,
     $  det_outfile*80, buffer*400,
     $  comments*100, surna*10, trajectory_file*200,
     $     start_idx_str*80, end_idx_str*80, jday_str*80,
     $     word(nw_max)*80

      integer*4 ra_col, dec_col, earth_delta_col, earth_mag_col, 

      logical keep_going, detectable


      ra_col = 17 - 8
      dec_col = 18 - 8
      earth_delta_col = 10 - 8
      earth_mag_col = 11 - 8

      lun_h = 10
      lun_t = 11
      lun_trajectory = 12
      code = 500
      gb = 0.15


      CALL getarg(1, distri_file)
      distri_file = trim(distri_file)
      CALL getarg(2, jday_str)
      read(jday_str, *) jday
      CALL getarg(3, jday_str)
      read(jday_str, *) obs_jday
      write(6,*) jday, obs_jday

      ext_index = index(distri_file,'.') - 1
      det_outfile = distri_file(1:ext_index)//'_'//jday_str//'.txt'
      write(*,*) 'Reading ',distri_file,' and writing output to ', 
     $ det_outfile

      open (unit=lun_h, file=det_outfile, status='REPLACE')
      open (unit=lun_t, file=distri_file, status='old')

C     write the header from the input distri_file to the det_outfile
      do while ( .true. )
         read (lun_t, '(a)') line
         if (line(1:1) == '#') then
            write(lun_h, '(a)') line
         else
            goto 1999
         end if
      end do
 1999 continue
      rierr=0

C     Get the location of the observer on the date of interest
      call ObsPos(code, obs_jday, epos, tmp, eos, ierr)

C     for each element in the distri_file compute position viewed from  epos
      do while ( rierr < 1 )
         call read_obj (distri_file, lun_t, a, e, inc, M,
     $        peri, node, h, q, extra, co, start_idx,
     $        end_idx, rierr)
         if ( rierr .ne. 0) then
            exit
         end if

c     Get the RA/DEC at survey date
         mt = M
     $        + (TwoPi/(a**1.5d0*365.25d0))*(obs_jday-jday)
         mt = mt - int(mt/TwoPi)*TwoPi

C        Get heliocentric X/Y/Z location at mean anomally mt         
         call pos_cart(a, e, inc, node, peri, mt, pos(1),
     $        pos(2), pos(3))
C        Compute heliocentric distance at obs_jday 
         call DistSunEcl(obs_jday, pos, r)
C        Compute the RA/DEC J2000 as seend from epos set previously
         call RADECeclXV(pos, epos, ground_delta, ra, dec)
c     Compute the Ground Based magnitude
         call AppMag(r, ground_delta, eos, h, gb, alpha, 
     $        ground_mag, ierr) 

C     Write the RA/DEC/distance and mag to extra vector
         write(extra(ra_col), '(f10.5)') ra/drad/15.0
         write(extra(dec_col), '(f10.5)') dec/drad
         write(extra(earth_delta_col), '(f10.3)') ground_delta
         write(extra(earth_mag_col), '(f10.3)') ground_mag

C     Write the new coordinates and mosition to the output file.
         write (lun_h, '(8(f8.3,1x))', advance='no') a, e, inc/drad, 
     $        node/drad, peri/drad, mt/drad, H, q
         do j = 1, co
            write (lun_h, '(a10,1x)', advance='no') extra(j)
         end do
         write(lun_h, *)

         8000 end do
      close (lun_h)


 9000 format (f8.3,1x,f6.3,1x,4(f8.3,1x),f8.1,1x,f16.1,1x)
 9001 format (f16.5,1x)
 9004 format (a16,1x)
 9002 format (6(f16.5,1x))
 9003 format (13(f16.5,1x))
 9006 continue
      end program xx

c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

      subroutine read_obj (filen, lun_in, a, e, i, capm,
     $  om, capom, h, q, extra, co, start_idx, end_idx, ierr)

c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
c This routine opens and reads in the object element file.
c Angles are returned in radian.
c Potentially use a common to return the H distribution parameters.
c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
c
c J-M. Petit  Observatoire de Besancon
c Version 1 : February 2004
c Version 2 : For L7 data release, June 2010
c
c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
c INPUT
c     filen : object element file name
c     lun_in: File unit
c
c OUTPUT
c     a     : Semi-major axis (R8)
c     e     : Eccentricity of orbit (R8)
c     i     : Inclination (R8)
c     capm  : Mean anomaly (R8)
c     om    : Argument of pericenter (R8)
c     capom : Longitude of node (R8)
c     h     : Absolute magnitude (R8)
c     jday  : Time of elements (R8)
c     extra : Array of values (10*R8)
c     co    : number of values in 'extra'
c     start_idx : first line to read
c     end_idx : last line to read
c     ierr  : Error code
c                0 : nominal run
c               10 : unable to open filen
c               20 : error reading record
c               30 : end of file reached
c-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-


      real*8
     $  a, e, i, capm, om, capom, h, Pi, drad, jday, jd, q

      integer*4
     $  nw_max, start_idx, end_idx

      parameter
     $  (Pi = 3.141592653589793238d0, drad = Pi/180.0D0, nw_max = 29)

      integer
     $  lun_in, ierr, j, nw, lw(nw_max), co, current_line

      character
     $     line*2000, filen*(*), word(nw_max)*80

      character*20 extra(20)

      logical
     $  opened

      data opened /.false./

      save opened, jd, current_line

      ierr = 0
      if (.not. opened) then
         open (unit=lun_in, file=filen, status='old', err=1000)
         opened = .true.
         jd = -1.d0
      end if

 1500 continue
      do j = 1, len(line)
         line(j:j) = ' '
      end do
      read (lun_in, '(a)', err=2000, end=3000) line
      if (line(1:1) .eq. '#') then
         goto 1500
      end if
      call parse (line, nw_max, nw, word, lw)
      if (nw .lt. 7) goto 2000
      read (word(1), *) a
      read (word(2), *) e
      read (word(3), *) i
      i = i*drad
      read (word(4), *) capom
      read (word(5), *) om
      read (word(6), *) capm
      read (word(7), *) h
      read (word(8), *) q
      capom = capom*drad
      om = om*drad
      capm = capm*drad
      if (nw .gt. 29) goto 2000
      do j = 9, nw
         read(word(j), *) extra(j-8)
      end do
      co = nw - 8
      return

 1000 continue
      ierr = 10
      return

 2000 continue
      ierr = 20
      return

 3000 continue
      ierr = 30
      close (lun_in)
      opened = .false.
      return


      end subroutine read_obj
