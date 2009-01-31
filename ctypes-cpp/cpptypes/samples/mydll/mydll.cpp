#include <stdio.h>
#include "mydll.h"

CSimpleClass::CSimpleClass(int value) : value(value) {
	printf("CSimpleClass(%p, %d)\n", this, value);
}

CSimpleClass::~CSimpleClass() {
	printf("~CSimpleClass(%p)\n", this);
}
void CSimpleClass::M1() {
	printf("C++/CSimpleClass::M1(%p)\n", this);
	V0();
	V1(value);
	V2();
}
void CSimpleClass::V0() {
	printf("C++/CSimpleClass::V0(%p)\n", this);
}
void CSimpleClass::V1(int x) {
	printf("C++/CSimpleClass::V1(%p, %d)\n", this, x);
}
void CSimpleClass::V1() {
	printf("C++/CSimpleClass::V1(%p)\n", this);
}
void CSimpleClass::V1(char *p) {
	printf("C++/CSimpleClass::V1(%p, %s)\n", this, p);
}
void CSimpleClass::V1(int x, char *p) {
	printf("C++/CSimpleClass::V1(%p, %d, %s)\n", this, x, p);
}
void CSimpleClass::V1(char *p, int x) {
	printf("C++/CSimpleClass::V1(%p, %s, %d)\n", this, p, x);
}
void CSimpleClass::V2() {
	printf("C++/CSimpleClass::V2(%p)\n", this);
}

void CSimpleClass::M1(int x) {
	printf("C++/CSimpleClass::M1(%p, %d)\n", this, x);
	if (x == -1)
		throw(x);
	if (x == -2)
		throw("foo bar");
	V0();
	V1(x);
	V2();
}
