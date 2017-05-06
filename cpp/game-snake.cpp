
#include <math.h>
#include <conio.h>
#include <windows.h>
#include <ctime>
#include <cstdio>
#include <cstdlib>
#include <vector>

using namespace std;

#define food 6666

void gotoxy(short x,short y) 
{ 
	COORD c={(short)(x<<1),(short)(y+1)};
	SetConsoleCursorPosition (GetStdHandle (STD_OUTPUT_HANDLE),c); 
}
void mark(int x,int y)
{
	gotoxy(x,y); printf("::");
}
void elim(int x,int y)
{
	gotoxy(x,y); printf("  ");
}

enum dirs{up,left,right,down};
const int dirs2x[]={0,-1,1,0};
const int dirs2y[]={-1,0,0,1};
const int dirs2kb[]={72,75,77,80};
int kb2dirs[256];

void globalInit()
{
	for(int x=0;x<256;x++)kb2dirs[x]=~0;
	kb2dirs[72]=0;
	kb2dirs[75]=1;
	kb2dirs[77]=2;
	kb2dirs[80]=3;
}

class snakebody
{
	vector<pair<int,int> > v;
public:
	pair<int,int> &operator[](size_t n){return v[n];};
	const pair<int,int> &operator[](size_t n)const{return v[n];};
	int getx(size_t n)const{return v[n].first;};
	int gety(size_t n)const{return v[n].second;};
	int getLastx()const{return v.back().first;};
	int getLasty()const{return v.back().second;};
	int getHeadx()const{return v[0].first;};
	int getHeady()const{return v[0].second;};
	void add(int x,int y)
	{
		v.push_back(pair<int,int>(0,0));
		move(x,y);
	}
	void move(int x,int y)
	{
		for(int z=v.size();--z;)
		{
			v[z]=v[z-1];
		}
		v[0]=pair<int,int>(x,y);
	}
	inline size_t size()const{return v.size();}
	inline resize(size_t n){v.resize(n);}
	inline resize(size_t n,const pair<int,int> &rhs){v.resize(n,rhs);}
};

class kbstat
{
	int a[4];
public:
	kbstat(){for(int x=0;x<4;x++)a[x]=0;}
	int getX()const{return a[2]-a[1];}
	int getY()const{return a[3]-a[0];}
	int &operator[](size_t x)
	{
		return a[x];
	}
	const int &operator[](size_t x)const
	{
		return a[x];
	}
	bool set()
	{
		if(kbhit())
		{
			int c=getch();
			for(int x=0;x<4;x++) a[x]=0;
			if(~kb2dirs[c]) a[kb2dirs[c]]=1;
			return c!=27;
		}
		return true;
	}
};

class env
{
	class ss
	{
	public:
		int dir;
		snakebody body; // x,y
		ss(){};
		ss(int initX,int initY){reset(initX,initY);};
		void clearblk()
		{
			for(int x=0,xs=body.size();x<xs;x++)
			{
				elim(getx(x),gety(x));
			}
		}
		void reset(int initX,int initY)
		{
			clearblk();
			dir=rand()&3;
			body.resize(1,pair<int,int>(initX,initY));
			mark(getHeadx(),getHeady());
		}
		inline int getx(size_t i)const{return body[i].first;}
		inline int gety(size_t i)const{return body[i].second;}
		inline int getHeadx()const{return body.getHeadx();}
		inline int getHeady()const{return body.getHeady();}
		inline int getLastx()const{return body.getLastx();}
		inline int getLasty()const{return body.getLasty();}
	}a;
	int ix,iy;
	int mx,my; // [0,m)
	int fx,fy;
	vector<vector<int> >mp;
	void drawEnv()
	{
		mp.resize(my,vector<int>(mx,0));
		for(int x=0;x<mx;x++){ mp[0][x]=1;    mark(x,0);    }
		for(int x=0;x<mx;x++){ mp[my-1][x]=1; mark(x,my-1); }
		for(int y=0;y<my;y++){ mp[y][0]=1;    mark(0,y);    }
		for(int y=0;y<my;y++){ mp[y][mx-1]=1; mark(mx-1,y); }
		mp[a.getHeady()][a.getHeadx()]=1;
	}
	void _reset()
	{
		a.reset(ix,iy);
		drawEnv();
		fx=rand()%(mx-2)+1;
		fy=rand()%(my-2)+1;
		mark(fx,fy);
		mp[fy][fx]=food;
	}
public:
	env(int mapX,int mapY,int initX,int initY){reset(mapX,mapY,initX,initY);}
	void reset(int mapX,int mapY,int initX,int initY)
	{
		mx=mapX;
		my=mapY;
		ix=initX;
		iy=initY;
		_reset();
	}
	inline void reset()
	{
		_reset();
	}
	bool movess(const kbstat&rhs) // return true if die
	{
		int gox=rhs.getX();
		int goy=rhs.getY();
		int hx=a.getHeadx(),hy=a.getHeady();
		switch(a.dir)
		{
		case dirs::up:
			if(gox) a.dir=gox<0?(int(dirs::left)):(int(dirs::right));
			break;
		case dirs::left:
			if(goy) a.dir=goy<0?(int(dirs::up)):(int(dirs::down));
			break;
		case dirs::right:
			if(goy) a.dir=goy<0?(int(dirs::up)):(int(dirs::down));
			break;
		case dirs::down:
			if(gox) a.dir=gox<0?(int(dirs::left)):(int(dirs::right));
			break;
		default:
			// ?
			break;
		}
		int newx=hx+dirs2x[a.dir],newy=hy+dirs2y[a.dir];
		if(mp[newy][newx]==1) return true;
		if(mp[newy][newx]==food)
		{
			// eat
			a.body.add(newx,newy);
			mp[newy][newx]=1;
		}
		else
		{
			// move
			int lx=a.body.getLastx(),ly=a.body.getLasty();
			elim(lx,ly);
			mp[ly][lx]=0;
			a.body.move(newx,newy);
			mark(newx,newy);
			mp[newy][newx]=1;
		}
		return false;
	}
	bool genFood()
	{
		vector<pair<int,int> >v;
		for(int y=0;y<my;y++) for(int x=0;x<mx;x++) if(mp[y][x]==0) v.push_back(pair<int,int>(x,y));
		int sz=v.size();
		if(sz<2) return true;
		if(mp[fy][fx]==food) return false;
		auto &t=v[rand()%sz];
		fx=t.first;
		fy=t.second;
		mp[fy][fx]=food;
		mark(fx,fy);
		return false;
	}
	int length()const{return a.body.size();}
};

int main(const int argc,const char *argv[])
{
	int mx=23,my=23; // use sscanf parse argv?
	int dt=333;
	globalInit();
	printf("esc to exit");
	env ee(mx,my,mx>>1,my>>1);
	kbstat kb;
	for(int flag=1;flag;)
	{
		gotoxy(mx>>1,my+1);printf("length: %d",ee.length());
		if(ee.genFood()){gotoxy(0,my+1);printf("win\n");break;};
		for(clock_t c=clock();flag&&c+dt>clock();flag=kb.set()) ;
		if(ee.movess(kb)){gotoxy(0,my+1);printf("lose\n");break;};
	}
	gotoxy(0,my+3);
}
