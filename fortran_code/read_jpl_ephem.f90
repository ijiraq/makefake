subroutine read_jpl_csv(iunit, jd, pos, vel, ierr)
  ! lookup line in ephemeris file (pointed to by iunit) with data close to jd and then use velocity
  ! to adjust the pos values to that requested.
  
  implicit none

  integer, intent(in) :: iunit
  real(kind=8), intent(in) :: jd
  real(kind=8), dimension(3), intent(out) :: pos, vel
  integer, intent(out) :: ierr

  character(len = 512) :: line
  character(len = 30) :: date
  real(kind=8) ejd
  integer :: iend, header_offset, ferr, offset
  logical :: read_header
  

  ! only read the header the first time we are called
  data read_header /.true./
  data header_offset /0/
  save read_header, header_offset


  ierr = 0
  if (read_header) then
     do
        read(iunit, '(A512)', end=999) line
        iend = len_trim(line)
        if ( line == '$$SOE' ) then
           read_header = .false.
           header_offset = FTELL(iunit)
           exit
        end if
     end do
  end if

  ! Loop through the ephemeris lines to get to the desired JD
  ! starting from line after the header
  offset = header_offset - FTELL(iunit) 
  CALL FSEEK(iunit, offset, 1, ferr)
  do
     read(iunit, '(A512)', end=999) line
     iend = len_trim(line)
     if ( line == '$$EOE' ) then
        ierr = 10
        return 
     end if     
     read(line(1:iend), '(F17.8,2X,A30,6(2X,F22.16))', err=998) ejd,  date, pos(1), pos(2), pos(3), vel(1), vel(2), vel(3)
     if ( ejd > jd) then
        pos = pos + vel*(jd-ejd)
        return
     end if
  end do
998 ierr = 10
999 return
end subroutine read_jpl_csv
