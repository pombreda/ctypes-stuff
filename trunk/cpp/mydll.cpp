#include <stdio.h>
#include "mydll.h"

CSimpleClass::CSimpleClass(int value) : value(value) {
	printf("CSimpleClass(%d)\n", value);
}

CSimpleClass::~CSimpleClass() {
	printf("~CSimpleClass\n");
}
void CSimpleClass::M1() {
	printf("C++/CSimpleClass::M1()\n");
	V0();
	V1(value);
	V2();
}
void CSimpleClass::V0() {
	printf("C++/CSimpleClass::V0()\n");
}
void CSimpleClass::V1(int x) {
	printf("C++/CSimpleClass::V1(%d)\n", x);
}
void CSimpleClass::V2() {
	printf("C++/CSimpleClass::V2()\n");
}

