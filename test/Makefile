OMNETPP_ROOT = /home/michael/omnetpp-6.0
SIMU5G_ROOT = /home/michael/5GTQ/Simu5G

INCLUDES = -I$(OMNETPP_ROOT)/include -I$(SIMU5G_ROOT)/src
LDFLAGS = -L$(OMNETPP_ROOT)/lib -L$(SIMU5G_ROOT)/src
LDLIBS = -lomnetpp -lsimu5g

CXXFLAGS = -v $(INCLUDES)

all: hello

hello: hello.o
	$(CXX) -o $@ $< $(LDFLAGS) $(LDLIBS)

hello.o: hello.cc
	$(CXX) -c $(CXXFLAGS) $<

clean:
	rm -f hello.o hello
