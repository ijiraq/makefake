
all: ClassyMakeFake Obj_At_Date

ClassyMakeFake: ClassyMakeFake.f utils.f
	gfortran -o ClassyMakeFake ClassyMakeFake.f
	
Obj_At_Date: Obj_At_Date.f SurveySubs.f
	gfortran -o Obj_At_Date Obj_At_Date.f


install: ClassyMakeFake Obj_At_Date
	cp ClassyMakeFake Obj_At_Date /arc/projects/classy/pipeline
