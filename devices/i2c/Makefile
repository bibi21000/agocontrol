LD = $(CXX)
#INCLUDES ?= -I/usr/inc/agocontrol/

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoi2c

agoi2c: agoi2c.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agoi2c  agoi2c.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agoi2c $(BINDIR)
