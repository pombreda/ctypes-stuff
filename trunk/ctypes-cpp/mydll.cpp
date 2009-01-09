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
void CSimpleClass::V2() {
	printf("C++/CSimpleClass::V2(%p)\n", this);
}

void CSimpleClass::M1(int x) {
	printf("C++/CSimpleClass::M1(%p, %d)\n", this, x);
}
