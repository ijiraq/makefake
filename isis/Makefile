
DBIMAGES = "/arc/projects/classy/dbimages/"
BINDIR = "/arc/projects/classy/pipeline"

scripts = *.sh *.py

install: $(scripts)
	cp isis.config $(DBIMAGES)/configs/
	cp swarp.config $(DBIMAGES)/configs/
	cp $(scripts) $(BINDIR)
