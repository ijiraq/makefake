
FC=gfortran

all: ClassyMakeFake Obj_At_Date

OBJ= utils.o read_jpl_ephem.o

%.o: %.f90
	$(FC) -c $< 

ClassyMakeFakeV4: ClassyMakeFakeV4.o $(OBJ)
	gfortran -o ClassyMakeFakeV4 -O3 ClassyMakeFakeV4.o $(OBJ)

HSCMakeFake: ClassyMakeFake.o $(OBJ)
	gfortran -o HSCMakeFake ClassyMakeFake.o $(OBJ)

JWSTMakeFake: JWSTMakeFake.o $(OBJ)
	gfortran -o JWSTMakeFake JWSTMakeFake.o $(OBJ)

Obj_At_Date: Obj_At_Date.f SurveySubs.f
	gfortran -o Obj_At_Date Obj_At_Date.f read_jpl_ephem.o


install: ClassyMakeFake Obj_At_Date
	cp ClassyMakeFake Obj_At_Date /arc/projects/classy/pipeline
