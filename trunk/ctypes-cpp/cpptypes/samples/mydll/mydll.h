#define EXPORT __declspec(dllexport)

struct COLOR {
	int red;
	int green;
	int blue;
	int alpha;
};

struct color {
	unsigned char red;
	unsigned char green;
	unsigned char blue;
	unsigned char alpha;
};

class EXPORT CSimpleClass {
  public:
	int value;
	CSimpleClass(int value);
	~CSimpleClass();
	void M1();
	void M1(int x) throw(int, char*) ;
	virtual void V0();
	virtual void V1(int x);
	virtual void V1();
	virtual void V1(char *ptr);
	virtual void V1(int x, char *ptr);
	virtual void V1(char *ptr, int x);
	virtual void V2();
	struct COLOR RGB(int red, int green, int blue, int alpha) {
		struct COLOR color = {red, green, blue, alpha};
		return color;
	}
	struct color rgb(unsigned char red,
			 unsigned char green,
			 unsigned char blue,
			 unsigned char alpha) {
		struct color c = {red, green, blue, alpha};
		return c;
	}
	virtual void Foo() = 0;
};
