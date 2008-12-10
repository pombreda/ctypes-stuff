class __declspec(dllexport) CSimpleClass {
  public:
	int value;
	CSimpleClass(int value);
	~CSimpleClass();
	void M1();
	virtual void V0();
	virtual void V1(int x);
	virtual void V2();
};
