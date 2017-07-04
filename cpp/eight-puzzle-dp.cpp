
/*

Eight-Puzzle solver - DynamicPrograming version
input format:

1 2 3
4 5 6
7 8 x

// x represents for empty block
// or in a line:

1 2 3 4 5 6 7 8 x

output:
a string directions(l,r,u,d) indicating where the empty block should go

*/

#include <stdio.h>
#include <vector>
#include <queue>
#define dsiz 100000000
#define finalstate 123456789
#define uppp 'u'
#define down 'd'
#define left 'l'
#define righ 'r'

using namespace std;

unsigned i;
int facto[10]={1};
int n,x;
int ini;
char tmp[10];
int used[10]={0};

int cnt(int n)
{
    used[n]=1;
    int x;
    int cnt;
    for(cnt=0,x=1;x<n;x++)
    {
        if(used[x]) continue;
        cnt++;
    }
    return cnt;
}
int convert(int data) //order
{
    int digi=dsiz;
    int num,x;
    for(num=0;num<10;num++) used[num]=0;
    for(num=0,x=8;digi;x--)
    {
        num+=cnt((data/digi)%10)*facto[x];
        digi/=10;
    }
    return num;
}
class state
{
public:
    int act,before,step;
    state(){act=0;before=-1;step=0;}
};
state sss[362880];
queue <int> q;

int findnine(int n)
{
    int digi=dsiz;
    while(digi)
    {
        if((n/digi)%10==9) break;
        digi/=10;
    }
    return digi;
}
void makedp()
{
    int v=q.front(),order;
    q.pop();
    int ori=v,convori=convert(v);
    int nine=findnine(v),tmp;
    if(nine!=100&&nine!=100000&&nine!=100000000) // right
    {
        tmp=(v/(nine*10))%10;
        v-=nine*9;
        v+=nine*tmp;
        v-=(nine*10)*tmp;
        v+=(nine*10)*9;
        order=convert(v);
        if(!sss[order].act)
        {
            sss[order].act=righ;
            sss[order].before=convori;
            sss[order].step=sss[convori].step+1;
            q.push(v);
        }
        v=ori;
    }
    if(nine<1000000) // down
    {
        tmp=(v/(nine*1000))%10;
        v-=nine*9;
        v+=nine*tmp;
        v-=(nine*1000)*tmp;
        v+=(nine*1000)*9;
        order=convert(v);
        if(!sss[order].act)
        {
            sss[order].act=down;
            sss[order].before=convori;
            sss[order].step=sss[convori].step+1;
            q.push(v);
        }
        v=ori;
    }
    if(nine>100) // up
    {
        tmp=(v/(nine/1000))%10;
        v-=nine*9;
        v+=nine*tmp;
        v-=(nine/1000)*tmp;
        v+=(nine/1000)*9;
        order=convert(v);
        if(!sss[order].act)
        {
            sss[order].act=uppp;
            sss[order].before=convori;
            sss[order].step=sss[convori].step+1;
            q.push(v);
        }
        v=ori;
    }
    if(nine!=1&&nine!=1000&&nine!=1000000) // left
    {
        tmp=(v/(nine/10))%10;
        v-=nine*9;
        v+=nine*tmp;
        v-=(nine/10)*tmp;
        v+=(nine/10)*9;
        order=convert(v);
        if(!sss[order].act)
        {
            sss[order].act=left;
            sss[order].before=convori;
            sss[order].step=sss[convori].step+1;
            q.push(v);
        }
        v=ori;
    }
}

int main()
{
    for(x=0;x<9;x++)
        facto[x+1]=facto[x]*(x+1);
    //cout<<convert(123456789)<<endl;
    //cout<<convert(987654321)<<endl;
    //cout<<findnine(123456789)<<endl;
    //cout<<findnine(912345678)<<endl;
    //
    q.push(123456789);
    while(q.size()) makedp();
    /* / show max-step states' orders
    vector <int> v;
    v.resize(0);
    x=0;
    for(i=1;i<362880;i++)
    {
        if(sss[x].step<sss[i].step)
        {
            x=i;
            v.resize(0);
            v.push_back(x);
        }
        else if(sss[x].step==sss[i].step)
        {
            v.push_back(i);
        }
    }
    for(i=0;i<v.size();i++)
        printf("%d ",v[i]);
    printf("\n");
    // */
    {
        while(1)
        {
            for(ini=0,x=0;x<9;x++)
            {
                ini*=10;
                scanf("%s",tmp);
                ini+= tmp[0]=='x'? 9:tmp[0]-'0';
            }
            i=convert(ini);
            //cout<<i<<endl;
            if(sss[i].act)
            {
                while(i)
                {
                    printf("%c",(char)sss[i].act);
                    i=sss[i].before;
                }
                printf("\n");
            }
            else printf("unsolvable\n");
        }
    }
    return 0;
}
