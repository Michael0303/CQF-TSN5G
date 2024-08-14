all: checkmakefiles
	@cd src && $(MAKE)

clean: checkmakefiles
	@cd src && $(MAKE) clean

cleanall: checkmakefiles
	@cd src && $(MAKE) MODE=release clean
	@cd src && $(MAKE) MODE=debug clean
	@rm -f src/Makefile

OMNETPP_ROOT = /home/michael/omnetpp-6.0/
INCLUDES = -I$(OMNETPP_ROOT)/include
CPPFLAGS = $(INCLUDES)


# generate the makefile by running opp_makemake in the src directory
# this command specifies several options:
# -f: force make to rebuild the makefile
# --make-so: generate a shared library
# -d: deep make, rebuild also dependent libraries
# -o tsnfivegcomm: output file name
# -O out: output directory
# -KINET_PROJ=$(INET_ROOT): specify the path to the inet library
# -DINET_IMPORT: tell opp_makemake to import the inet library
# -I. -I$(INET_ROOT)/src -L$(INET_ROOT)/src -lINET$(D): specify the inet library to link against
# -KSIMU5G_PROJ=$(SIMU5G_ROOT): specify the path to the simu5g library
# -DSIMU5G_IMPORT: tell opp_makemake to import the simu5g library
# -I. -I$(SIMU5G_ROOT)/src -L$(SIMU5G_ROOT)/src -lsimu5g$(D): specify the simu5g library to link against
makefiles:
	@cd src && opp_makemake --make-so -f --deep -o testout -O out -KINET_PROJ=$(INET_ROOT) -DINET_IMPORT -I$(CPPFLAGS) -I. -I$(INET_ROOT)/src -L$(INET_ROOT)/src -lINET$(D) -KSIMU5G_PROJ=$(SIMU5G_ROOT) -DSIMU5G_IMPORT -I. -I$(SIMU5G_ROOT)/src -L$(SIMU5G_ROOT)/src -lsimu5g$(D)
checkmakefiles:
	@if [ ! -f src/Makefile ]; then \
	echo; \
	echo '======================================================================='; \
	echo 'src/Makefile does not exist. Please use "make makefiles" to generate it!'; \
	echo '======================================================================='; \
	echo; \
	exit 1; \
	fi