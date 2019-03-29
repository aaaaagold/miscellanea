#include <iostream>

using namespace std;

class obj
{
public:
	obj(){ cout<<"construct obj"<<endl; }
	~obj(){ cout<<"destruct obj"<<endl; }
};

class A
{
	obj o;
public:
	A(){ cout<<"construct A"<<endl; }
	virtual ~A()=default;
	virtual void foo()=0;
	void foo2(){ cout<<"A"<<endl; }
};

class B :public A
{
public:
	B(){ cout<<"construct B"<<endl; }
	~B(){ cout<<"destruct B"<<endl; }
	void foo(){ cout<<"B"<<endl; }
};

class C :public A
{
	obj o;
public:
	C(){ cout<<"construct C"<<endl; }
	~C(){ cout<<"destruct C"<<endl; }
	void foo(){ cout<<"C"<<endl; }
};


int main()
{
	ios::sync_with_stdio(false);
	cin.tie(NULL);
	const char * const sep=" **** ";
	
	A *ptrB=NULL,*ptrC=NULL;
	cout<<sep<<"new B"<<sep<<endl;
	ptrB=new B();
	cout<<sep<<"new C"<<sep<<endl;
	ptrC=new C();
	cout<<sep<<"ptrB->foo()"<<sep<<endl;
	ptrB->foo();
	cout<<sep<<"ptrC->foo()"<<sep<<endl;
	ptrC->foo();
	cout<<sep<<"ptrB->foo2()"<<sep<<endl;
	ptrB->foo2();
	cout<<sep<<"ptrC->foo2()"<<sep<<endl;
	ptrC->foo2();
	cout<<sep<<"delete ptrB"<<sep<<endl;
	delete ptrB;
	cout<<sep<<"delete ptrC"<<sep<<endl;
	delete ptrC;
	
	cout<<"return 0"<<endl;
	return 0;
}
