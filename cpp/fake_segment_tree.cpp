// need to overload + and -
#include <stdio.h>

template<class T>
class segtree
{
    T **tree;
    size_t *sizes;
    size_t lv;
    size_t sizen;
    T before(size_t end)
    {
        if(end>=sizen) return tree[lv-1][0];
        if(end==0) return T(NULL);
        const size_t one=1;
        size_t rmb=0; // right most bit===1<<rmb
        T rtv(T(NULL));
        while(end)
        {
            size_t tmp=end&(-end); // magic with 2's complement
            for(;(tmp&(one<<rmb))==0;++rmb)
                ;
            rtv+=tree[rmb][(end>>rmb)-1];
            end-=tmp;
        }
        return rtv;
    }
public:
    segtree():tree(NULL),sizes(NULL),lv(0),sizen(0)
    {
        ;
    }
    segtree(const T *arr,const size_t &n):tree(NULL),sizes(NULL),lv(0),sizen(0)
    {
        init(arr,n);
    }
    ~segtree()
    {
        if(tree)
        {
            for(size_t x=0,size=lv;x!=size;++x)
            {
                register T *tmp=tree[x];
                if(tmp)
                    delete [] tmp;
            }
            delete [] tree;
        }
        if(sizes) delete [] sizes;
    }
    void init(const T *arr,const size_t &n)
    {
        this->~segtree();
        if(n==0)
            return;
        sizen=n;

        register size_t lvcnt=1;
        for(size_t x=n;x!=1;x=(x>>1)+(x&1),++lvcnt)
            ;
        lv=lvcnt;

        if((sizes=new size_t[lvcnt]))
            for(size_t m=n,x=0;x!=lvcnt;m=(m>>1)+(m&1),++x)
                sizes[x]=m;
        else return;

        if((tree=new T*[lvcnt]))
        {
            for(register size_t m=n,x=0;x!=lvcnt;m=(m>>1)+(m&1),++x)
                tree[x]=new T[m];

            register T *pre,*now=tree[0];
            register size_t s0,s1=n;
                for(register size_t x=0;x!=s1;++x)
                    now[x]=arr[x];
            for(size_t y(1);y!=lvcnt;++y)
            {
                s0=s1;
                s1=sizes[y];
                pre=now;
                now=tree[y];
                if((s0&1)==1)
                {
                    --s1;
                    for(register size_t x=0;x!=s1;++x)
                        now[x]=pre[x<<1]+pre[(x<<1)|1];
                    now[s1++]=pre[s0-1];
                }
                else
                {
                    for(register size_t x=0;x!=s1;++x)
                        now[x]=pre[x<<1]+pre[(x<<1)|1];
                }
            }
        }
        else return;
    }
    T query(size_t begin,size_t end)
    {
        return before(end)-before(begin);
    }
    void alter(size_t target,const T &setas)
    {
        if(target>=sizen) return;
        T delta=setas-tree[0][target];
        for(int x=0;x<lv;++x)
            tree[x][target>>x]+=delta;
    }
    void print() // debug
    {
        for(int y=0;y<lv;++y)
        {
            for(int x=0,s=sizes[y];x<s;++x)
                printf(" %d",tree[y][x]);
            printf("\n");
        }
    }
    int verify() // debug
    {
        int error=0;
        register T *ptr=tree[0];
        for(size_t b=0;b++<sizen;)
            for(size_t e=b-1;e++<sizen;)
            {
                T sss(T(NULL));
                for(register size_t x=b;x<e;++x)
                    sss+=ptr[x];
                if(query(b,e)!=sss) error++;
            }
        return error;
    }
};

int main(const int argc,const char *argv[])
{
    int tmp,flag=0;
    if(argc==2) flag=sscanf(argv[1],"%d",&tmp);
    flag=(flag==1)&&(tmp<31);
    const int length=flag?tmp:30;
    int arr[length];
    for(int x=0;x<length;++x)
        arr[x]=1<<x;

    segtree<int>s(arr,length);

    printf("array length:");if(flag==0)printf("(default) "); printf("%d\n",length);
    printf("tree:");printf("\n");
    s.print();

    printf("error:");printf("%d\n",s.verify());
    int error=0;
    for(int x=0;x<length;++x)
    {
        printf("alter:[%d]=",x);printf("%d\n",-arr[x]);
        s.alter(x,-arr[x]);
        //printf("tree:");printf("\n");
        //s.print();
        printf("error:");printf("%d\n",error+=s.verify());
    }
    printf("total errors:");printf("%d\n",error);
    return 0;
}

