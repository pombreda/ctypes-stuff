#define EXPORT __declspec(dllexport)

class EXPORT CSimpleClass {
  public:
	int value;
	CSimpleClass(int value);
	~CSimpleClass();
	void M1();
	void M1(int x);
	virtual void V0();
	virtual void V1(int x);
	virtual void V1();
	virtual void V1(char *ptr);
	virtual void V1(int x, char *ptr);
	virtual void V1(char *ptr, int x);
	virtual void V2();
};
