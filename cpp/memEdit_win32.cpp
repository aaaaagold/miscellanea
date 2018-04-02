
// g++ -o a.cpp.exe --all-warnings -std=c++11 -O2 -s a.cpp "C:\Windows\System32\psapi.dll" -lPsapi

// M$:
// To ensure correct resolution of symbols, add Psapi.lib to TARGETLIBS
// and compile with -DPSAPI_VERSION=1


#define ull unsigned long long
#define _debug

#include <cstdio>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include <iostream>
#include <sstream>
#include <fstream>
#include <iomanip>

#include <windows.h>
#include <psapi.h>

using namespace std;

inline void debug(const string &s)
{
	#ifdef _debug
	cerr<<s<<endl;
	#endif
	return;
}

void usage()
{
	printf("usage:  arg0  [ -l[options] | -a pid ]\n");
	printf("\t a option can be:\n");
	printf("\t\t u\t list unknown name processes\n");
	printf("\t\t n\t sorted by name\n");
	printf("\t\t p\t sorted by pid\n");
	printf("\t\t * You cannot use 'n', 'p' at same time.  The last you put will be considered. \n");
}

bool prefixEq(const string &prefixStr,const string &fullStr){
	const char *prefix=prefixStr.c_str(),*full=fullStr.c_str();
	for(;(*prefix)!=0 && (*full)!=0;prefix++,full++){
		if((*prefix)!=(*full)) return false;
	}
	return (*prefix)==0;
}

vector< pair<ull,string> > sysListProc(bool unknown=0)
{
	vector< pair<ull,string> > rtv;
	DWORD aProcesses[65536];
	unsigned cProcesses=0;
	{
		DWORD cbNeeded;
		// Get the list of process identifiers.
		if ( !EnumProcesses( aProcesses, sizeof(aProcesses), &cbNeeded ) )
		{
			cerr<<" error: fail: sysListProc "<<endl;
			return rtv;
		}
		// Calculate how many process identifiers were returned.
		cProcesses = cbNeeded;  cProcesses /= sizeof(DWORD);
	}

	// Print the name and process identifier for each process.
	for ( unsigned i = 0; i < cProcesses; i++ ) if( aProcesses[i] != 0 ) {
		DWORD processID=aProcesses[i];
		const TCHAR unknownName[] = TEXT("<unknown>");
		TCHAR szProcessName[MAX_PATH<<1] = TEXT("<unknown>");
		
		// Get a handle to the process.
		HANDLE hProcess = OpenProcess( PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, processID );
		// Get the process name.
		if (NULL != hProcess )
		{
			HMODULE hMod;
			DWORD cbNeeded;
			if ( EnumProcessModules( hProcess, &hMod, sizeof(hMod), &cbNeeded) )
			{
				GetModuleBaseName( hProcess, hMod, szProcessName, sizeof(szProcessName)/sizeof(TCHAR) );
			}
		}
		// Release the handle to the process.
		CloseHandle( hProcess );
		// Print the process name and identifier.
		if(unknown || strcmp(unknownName,szProcessName)!=0)
			rtv.push_back(pair<ull,string>(processID,szProcessName));
	}
	return rtv;
}

bool listProcesses(bool unknown=0,int sortedLv=0) // return true on error
{
	vector< pair<ull,string> > pList=sysListProc(unknown);
	if(pList.size()==0){return 1;}
	switch(sortedLv)
	{
	default:
	case 0:
	{ // do nothing
	}break;
	case 1: // sorted by pid
	{
		sort(pList.begin(),pList.end());
	}break;
	case 2: // sorted by name
	{
		vector< pair<string,ull> > pList1;
		for(auto it=pList.begin();it!=pList.end();++it)
			pList1.push_back( pair<string,ull >((*it).second,(*it).first) );
		sort(pList1.begin(),pList1.end());
		for(size_t x=pList.size();x--;)
			pList[x]=pair<ull,string >(pList1[x].second,pList1[x].first);
	}break;
	}
	for(auto it=pList.begin();it!=pList.end();++it)
		printf("PID: %6llu  %s\n" ,(*it).first ,(*it).second.c_str() );
	return 0;
}

template<class T>
using pv = pair<T*,T>;

template<class T>
void printPV(const pv<T> &rhs)
{
	stringstream ss;
	string s;
	ss << internal << setfill('0') << setw((sizeof(rhs.first)<<1)+2) << rhs.first;
	ss>>s;
	printf("%s: %d\n",s.c_str(),rhs.second);
}

class attacher
{
	bool valid;
	ull pid;
	HANDLE hProcess;
	void construct()
	{
		valid=0;
		hProcess=NULL;
	}
	void destruct()
	{
		release();
	}
public:
	attacher(){construct();}
	attacher(ull processID){construct();attach(processID);}
	~attacher(){destruct();}
	bool good()const{return valid;}
	void release()
	{
		if(hProcess!=NULL) CloseHandle( hProcess );
	}
	bool attach(ull processID) // return true on error
	{
		release();
		hProcess = OpenProcess( PROCESS_QUERY_INFORMATION | PROCESS_ALL_ACCESS, FALSE, processID );
		pid=processID;
		valid=hProcess!=NULL;
		return !valid;
	}
	void edit_int(int *const ptr,const int val)const
	{
		if(!WriteProcessMemory(hProcess, (LPVOID)ptr, &val, sizeof(val), 0))
			cerr<<" error: fail: WriteProcessMemory"<<endl;
	}
	vector<pv<int> > search_int_re(const vector<pv<int> > &prevRes,const int val,bool rtvAll=false)const
	{
		vector<pair<int*,int> > rtv;
		if(prevRes.size()==0) return rtv;
		// win mem page size = 4K
		const int buffsizeMinRaw=1<<12;
		const int buffsizeMinInt=buffsizeMinRaw/sizeof(int);
		const int buffsizeMinByte=buffsizeMinInt*sizeof(int);
		vector<int> buffMin(buffsizeMinInt);
		// collect page bases
		vector<vector<int*> > pg;
		for(int *ptr=0,x=0,xs=prevRes.size();x!=xs;x++)
		{
			while(prevRes[x].first>=ptr+buffsizeMinInt) ptr+=buffsizeMinInt;
			if(prevRes[x].first>=ptr && prevRes[x].first<ptr+buffsizeMinInt)
			{
				pg.push_back(vector<int*>(1,ptr));
				ptr+=buffsizeMinInt;
			}
			pg.back().push_back(prevRes[x].first);
		}
		// search
		for(size_t g=0,gs=pg.size();g!=gs;g++)
		{
			int *const ptrMin=pg[g][0];
			if(ReadProcessMemory(hProcess,(LPVOID)ptrMin, &buffMin[0], buffsizeMinByte, 0))
			{
				for(size_t t=1,ts=pg[g].size();t!=ts;t++)
				{
					int x=pg[g][t]-ptrMin;
					int *const ptr2=ptrMin+x;
					int res=buffMin[x];
					if(rtvAll || res==val)
					{
						rtv.push_back(pv<int>(ptr2,res));
					}
				}
			}
		}
		printf("result count: %llu\n",(ull)(rtv.size()));
		return rtv;
	}
	vector<pv<int> > search_int(const int val)const
	{
		vector<pv<int> > rtv;
		// win mem page size = 4K
		const int buffsizeMinRaw=1<<12;
		const int buffsizeMinInt=buffsizeMinRaw/sizeof(int);
		const int buffsizeMinByte=buffsizeMinInt*sizeof(int);
		vector<int> buffMin(buffsizeMinInt);
		// larger, faster
		const int buffsizeRaw=max(1<<16,buffsizeMinRaw);
		const int buffsizeInt=buffsizeRaw/sizeof(int);
		const int buffsizeByte=buffsizeInt*sizeof(int);
		vector<int> buff(buffsizeInt);
		for(int *ptr=0,*last=(int*)0x7F000000;ptr<last;ptr+=buffsizeInt)
		{
			// "If the function succeeds, the return value is nonzero."
			if(ReadProcessMemory(hProcess,(LPVOID)ptr, &buff[0], buffsizeByte, 0))
			{
				for(int x=0;x!=buffsizeInt;x++)
				{
					int *const ptr2=ptr+x;
					int res=buff[x];
					if(res==val)
					{
						rtv.push_back(pv<int>(ptr2,res));
					}
				}
			}else for(int *ptrMin=ptr,*lastMin=ptrMin+buffsizeInt;ptrMin<lastMin && ptrMin<last;ptrMin+=buffsizeMinInt){
				if(ReadProcessMemory(hProcess,(LPVOID)ptrMin, &buffMin[0], buffsizeMinByte, 0))
				{
					for(int x=0;x!=buffsizeMinInt;x++)
					{
						int *const ptr2=ptrMin+x;
						int res=buffMin[x];
						if(res==val)
						{
							rtv.push_back(pv<int>(ptr2,res));
						}
					}
				}
			}
		}
		printf("result count: %llu\n",(ull)(rtv.size()));
		return rtv;
	}
	ull getPid()const
	{
		return pid;
	}
	HANDLE getHandle()const
	{
		return hProcess;
	}
};

class exp
{
	class token
	{
	public:
		int type; // 0:undef  1:num  2:op
		int val;
		token(){}
		token(int t,int v){init(t,v);}
		token &init(int t,int v)
		{
			type=t;val=v;
			return *this;
		}
	};
	static bool isDigit(int c){ return c<='9' && '0'<=c; }
	static vector<token> tk1(const string &s)
	{
		// 14351 526-51() =25 -=q4 [][] \5233
		vector<token> rtv;
		string tmp="";
		int stat=0; // 0: none  1: num
		const char *ptr=s.c_str();
		for(unsigned char c=*ptr;;c=*(++ptr))
		{
			if(isDigit(c)) stat=1;
			else if(stat==1)
			{
				int v; sscanf(tmp.c_str(),"%d",&v);
				rtv.push_back(token(1,v)); tmp="";
				stat=0;
			}
			if(c==0) break;
			if(c<=32) continue;
			switch(stat)
			{
			case 0:
			{
				rtv.push_back(token(2,c));
			}break;
			case 1:
			{
				tmp+=c;
			}break;
			}
		}
		return rtv;
	}
	static vector<token> tk2(vector<token> &&tkv)
	{
		vector<token> &v=tkv; v.push_back(token(0,0));
		vector<token> rtv;
		int coef=1;
		unsigned stat=1; // 1:get num  2:get op
		for(unsigned x=0;v[x].type!=0;x++){ const auto &t=v[x]; switch(stat) {
		case 1:
		{
			if(t.type==1){ rtv.push_back(token(1,coef*t.val)); coef=1; stat=2; }
			else if(t.type==2) switch(t.val){
			case '-':
				coef=-coef;
			case '+':
				break;
			case '/':
			case '*':
				rtv.resize(0); return rtv; 
			}
		}	break;
		case 2:
		{
			if(t.type==1){ rtv.resize(0); return rtv; }
			else if(t.type==2){ rtv.push_back(t); stat=1; }
		}	break;
		}}
		if(stat!=2) rtv.resize(0);
		return rtv;
	}
	static int tk3(const vector<token> &v, unsigned strt=0, unsigned opp=0)
	{
		vector<int> n;
		vector<int> o;
		for(unsigned x=0,xs=v.size();x<xs;x++)
		{
			if((x&1)==0){ n.push_back(v[x].val); continue; }
			switch(v[x].val)
			{
			case '-':
			case '+':
				 o.push_back(v[x].val);
			break;
			case '/':
				n.back()/=v[++x].val;
			break;
			case '*':
				n.back()*=v[++x].val;
			break;
			}
		}
		for(unsigned x=0,xs=o.size();x<xs;x++)
		{
			switch(o[x])
			{
			case '-': n[0]-=n[x+1]; break;
			case '+': n[0]+=n[x+1]; break;
			}
		}
		return n[0];
	}
public:
	static vector<int> parseInt(stringstream &ss)
	{
		string s,tmp; while(ss>>tmp) s+=tmp;
		vector<int> rtv;
		const auto &res=tk2(tk1(s));
		if(res.size()!=0) rtv.push_back(tk3(res));
		return rtv;
	}
};

class hack
{
	attacher hdl;
	vector<vector<pv<int> > > ptrv_prev;
	vector<pv<int> > ptrv;
	bool attach_qv;  // 0: quiet  1: verbose
	static void attach_inerr(const string &s)
	{
		printf("input error:%s\n",s.c_str());
	}
	/* /
	static vector<int> parseExp_int_simple(const string &lhs, const string &op, const string &rhs)
	{
		vector<int> rtv(2);
		if(sscanf(lhs.c_str(),"%d",&rtv[0])!=1){ attach_inerr(lhs); rtv.resize(0); }
		else if(op!="")
		{
			if(op!="*" && op!="+" && op!="-" && op!="/"){ attach_inerr(op); rtv.resize(0); }
			else if(sscanf(rhs.c_str(),"%d",&rtv[1])!=1){ attach_inerr(rhs); rtv.resize(0); }
			else switch(op[0])
			{
			default: break;
			case '*': rtv[0]*=rtv[1]; break;
			case '+': rtv[0]+=rtv[1]; break;
			case '-': rtv[0]-=rtv[1]; break;
			case '/': rtv[0]/=rtv[1]; break;
			}
		}
		return rtv;
	}
	// */
	static vector<pv<int> > attach_parseAddrList(stringstream &ss) // return [(NULL,0)] on error
	{
		vector<pv<int> > rtv;
		string s;
		int *ptr;
		while(ss>>s)
		{
			if(prefixEq("0x",s) && sscanf(s.c_str(),"0x%p",&ptr)==1) rtv.push_back(pv<int>(ptr,0));
			else
			{
				attach_inerr(s); // printf("input error:%s\n",s.c_str());
				rtv.resize(0); rtv.push_back(pv<int>(0,0));
				break;
			}
		}
		return rtv;
	}
	void attach_view(stringstream &ss)const
	{
		if(attach_qv) printf("view result\n");
		vector<pv<int> > tmpv=attach_parseAddrList(ss);
		sort(tmpv.begin(),tmpv.end());
		if(tmpv.size()>0 && tmpv[0].first!=NULL ) tmpv=hdl.search_int_re(tmpv,0,1);
		else if(tmpv.size()==0) tmpv=ptrv;
		for(unsigned x=0,xs=tmpv.size();x!=xs;x++) printPV(tmpv[x]);
	}
public:
	hack(){init();}
	hack(ull pid){init();attach(pid);}
	void init()
	{
		attach_qv=1;
	}
	bool attach(ull pid) // includes cli
	{
		hdl.attach(pid);
		if(!hdl.good()){ cerr<<" error: fail: attach "<<endl; return 1; }
		for(string cmd;printf("> "),1;)
		{
			if(!getline(cin,cmd) || cmd=="quit") for(printf("sure to quit? (Y/N) \n");1;){
				cin.sync();  cin.clear(); // OwO
				bool invalid=0;
				if(!getline(cin,cmd) || (cmd[0]!='Y' && cmd[0]!='N')) invalid=1;
				if(invalid) printf("please input Y or N: ");
				else if(cmd[0]=='N') break;
				else return 0;
			}
			if(cmd.size()==0) continue;
			stringstream ss; ss<<cmd;
			string act; ss>>act;
			if(act=="help"){
				const char *const addrList="[ ADDR [ ADDR ] ... ]";
				printf("commands:\n");
				printf("  %-7s\n",                           "help");
				printf("    %-7s\n","print this");
				printf("  %-7s\n",                           "quiet");
				printf("    %-7s\n","do not repeat what you are doing");
				printf("  %-7s\n",                           "verbose");
				printf("    %-7s\n","repeat what you are doing");
				printf("  %-7s  %-7s\n",                     "view",addrList);
				printf("    %-7s\n","view (address,value) pair");
				printf("    %-7s\n","default: current stack");
				printf("  %-7s\n",                           "update");
				printf("    %-7s\n","update cached (address,value) pair from 'ns' or 'rs'");
				printf("  %-7s  %-7s\n",                     "updateview",addrList);
				printf("    %-7s\n","combined cmd of update and view, 'uv' in short");
				printf("    %-7s\n","default: current stack");
				printf("  %-7s  %-7s  %-7s\n",               "ns","TYPE","VALUE");
				printf("    %-7s\n","new search");
				printf("    %-7s\n","write result to current stack");
				printf("  %-7s  %-7s  %-7s\n",               "rs","TYPE","VALUE");
				printf("    %-7s\n","re-search (from last result)");
				printf("    %-7s\n","write result to current stack");
				printf("  %-7s  %-7s  %-7s  %-7s  %-7s\n",   "e","TYPE","LOC","METHOD","expression_without_quote");
				printf("    %-7s\n","edit memory");
				printf("  %-7s  %-7s\n",                     "a",addrList);
				printf("    %-7s\n","add ADDRs to current stack");
				printf("  %-7s\n",                           "clear");
				printf("    %-7s\n","clear current stack");
				printf("  %-7s\n",                           "push");
				printf("    %-7s\n","push current stack to stack list");
				printf("  %-7s\n",                           "ls");
				printf("    %-7s\n","list size");
				printf("  %-7s\n",                           "la");
				printf("    %-7s\n","list all stack size");
				printf("  %-7s\n",                           "sc");
				printf("    %-7s\n","view stack counts");
				printf("  %-7s\n",                           "ss");
				printf("    %-7s\n","select stack, this will overwrite current stack");
				printf("  %-7s  %-7s\n",                     "delete","int_number");
				printf("    %-7s\n","delete a stack in stack list (index starts from 0)");
				printf("\n");
				printf("  %-7s can be:\n","ADDR");
				printf("    %-7s\n","0x... except 0x0..0");
				printf("  %-7s can be:\n","TYPE");
				printf("    %-7s\n","int");
				printf("  %-7s can be:\n","LOC");
				printf("    %-7s\n","ADDR");
				printf("    %-7s\n","ALL");
				printf("  %-7s can be:\n","METHOD");
				printf("    %-7s\n","a(bsolute)");
				printf("    %-7s\n","d(elta)");
			}else if(act=="quiet"){
				printf("switch to quiet mode\n");
				attach_qv=0;
			}else if(act=="verbose"){
				printf("switch to verbose mode\n");
				attach_qv=1;
			}else if(act=="v" || act=="view"){
				if(attach_qv) printf("view (ptrs,cached value)s\n");
				attach_view(ss);
			}else if(act=="u" || act=="update"){
				if(attach_qv) printf("update cached values\n");
				ptrv=hdl.search_int_re(ptrv,0,1);
			}else if(act=="uv" || act=="updateview"){
				if(attach_qv) printf("update and view\n");
				ptrv=hdl.search_int_re(ptrv,0,1);
				attach_view(ss);
			}else if(act=="ns"){
				if(attach_qv) printf("new search\n");
				string type; ss>>type;
				if(type=="int")
				{
					string val; ss>>val;
					int tmp;
					if(sscanf(val.c_str(),"%d",&tmp)==1)
					{
						// ptrv_prev=ptrv;
						ptrv=hdl.search_int(tmp);
					}
					else  attach_inerr(val);
				}else printf("unknown %s type: %s\n","search",type.c_str());
			}else if(act=="rs"){
				if(attach_qv) printf("re-search\n");
				string type; ss>>type;
				if(type=="int")
				{
					string val; ss>>val;
					int tmp;
					if(sscanf(val.c_str(),"%d",&tmp)==1)
					{
						// ptrv_prev=ptrv;
						ptrv=hdl.search_int_re(ptrv,tmp);
					}
					else  attach_inerr(val);
				}else printf("unknown %s type: %s\n","search",type.c_str());
			}else if(act=="e"){
				if(attach_qv) printf("edit\n");
				string type; ss>>type;
				if(type=="int")
				{
					string loc,method,exp1,op,exp2; ss>>loc>>method;
					int *ptr,tmp;
					bool padding=0,err=0;
					if(method=="a" || method=="absolute") padding=0;
					else if(method=="d" || method=="delta") padding=1;
					else err=1;
					vector<int> val=exp::parseInt(ss);
					if(err) attach_inerr(loc+" "+method);
					else if(prefixEq("0x",loc) && sscanf(loc.c_str(),"0x%p",&ptr)==1 && val.size()!=0)
					{
						tmp=val[0];
						if(padding) tmp+=hdl.search_int_re(vector<pv<int> >(1,pv<int>(ptr,0)),0,1)[0].second;
						hdl.edit_int(ptr,tmp);
					}
					else if((loc=="A" || loc=="ALL") && val.size()!=0)
					{
						tmp=val[0];
						if(padding) ptrv=hdl.search_int_re(ptrv,0,1);
						for(size_t x=ptrv.size();x--;) hdl.edit_int(ptrv[x].first,padding?ptrv[x].second+tmp:tmp);
					}
					else attach_inerr(string()+"loc err  or  exp err: "+ss.str());
				}else printf("unknown %s type: %s\n","edit",type.c_str());
			}else if(act=="a"){
				if(attach_qv) printf("add addr\n");
				vector<pv<int> > tmpv=attach_parseAddrList(ss);
				sort(tmpv.begin(),tmpv.end());
				if(tmpv.size()>0 && tmpv[0].first!=NULL ) tmpv=hdl.search_int_re(tmpv,0,1);
				else tmpv.resize(0);
				printf("add %u addresses\n",(unsigned)(tmpv.size()));
				for(size_t x=0,xs=tmpv.size();x<xs;x++) ptrv.push_back(tmpv[x]);
				sort(ptrv.begin(),ptrv.end());
				printf("current stack size: %u\n",(unsigned)(ptrv.size()));
			}else if(act=="clear"){
				if(attach_qv) printf("clear current\n");
				ptrv.resize(0);
			}else if(act=="push"){
				if(attach_qv) printf("push stack to list\n");
				ptrv_prev.push_back(ptrv);
			}else if(act=="ls"){
				if(attach_qv) printf("list size\n");
				printf("number available: [0,%u)\n", (unsigned)(ptrv_prev.size()) );
			}else if(act=="la"){
				if(attach_qv) printf("list all stack size\n");
				printf("in list\n");
				for(unsigned x=0,xs=ptrv_prev.size();x!=xs;x++)
					printf("%11u: %u\n" ,x ,(unsigned)(ptrv_prev[x].size()) );
				printf("current: %u\n",(unsigned)(ptrv.size()));
			}else if(act=="ss"){
				if(attach_qv) printf("select from stack\n");
				string val; ss>>val;
				unsigned n;
				if(sscanf(val.c_str(),"%u",&n)==1 && n<ptrv_prev.size()) ptrv=ptrv_prev[n];
				else attach_inerr(val);
			}else if(act=="delete"){
				if(attach_qv) printf("del\n");
				string val; ss>>val;
				unsigned n;
				if(sscanf(val.c_str(),"%u",&n)==1 && n<ptrv_prev.size())
				{
					for(size_t x=n,xs=ptrv_prev.size();++x<xs;)
						ptrv_prev[x-1]=std::move(ptrv_prev[x]);
					ptrv_prev.pop_back();
				}
				else attach_inerr(val);
			}
			else printf("unknown command: %s\n try help\n",act.c_str());
		}
		return 0;
	}
};


int main(const int argc,const char *argv[])
{
	bool printUsage=0;
	if(argc==1){ printUsage=1; }
	else if(argv[1][0]!='-') printUsage=1;
	else
	{
		switch(argv[1][1])
		{
		default: printUsage=1; break;
		case 'a':
		{
			ull pid;
			hack h;
			if(argc>2 && sscanf(argv[2],"%llu",&pid)==1) h.attach(pid);
			else printUsage=1;
		}break;
		case 'l':
		{
			bool unknown=0;
			int sortedLv=0;
			for(const char *ptr=argv[1];*(++ptr);)
			{
				if((*ptr)=='u') unknown=1;
				if((*ptr)=='p') sortedLv=1;
				if((*ptr)=='n') sortedLv=2;
			}
			listProcesses(unknown,sortedLv);
		}break;
		}
	}
	if(printUsage) usage();
	return 0;
}
