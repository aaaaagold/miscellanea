#include <bits/stdc++.h>
using namespace std;

using Pair = pair<int, int>;   // {min, max}

struct SegTree {
    int n;
    vector<Pair> tree;   // size 2n；葉子在 tree[n .. 2n-1]

    static Pair merge(const Pair& a, const Pair& b) {
        return {min(a.first, b.first), max(a.second, b.second)};
    }

    // build：由下往上推
    explicit SegTree(const vector<int>& a) {
        n = (int)a.size();
        tree.assign(2 * n, {INT_MAX, INT_MIN});   // identity
        for (int i = 0; i < n; i++)
            tree[n + i] = {a[i], a[i]};           // 葉子
        for (int i = n - 1; i > 0; i--)           // 由下往上 build
            tree[i] = merge(tree[i << 1], tree[(i << 1) | 1]);
    }

    // 單點更新 a[pos] = val
    void update(int pos, int val) {
        pos += n;
        tree[pos] = {val, val};
        while (pos > 1) {                          // 一路往上推到根
            pos >>= 1;
            tree[pos] = merge(tree[pos << 1], tree[(pos << 1) | 1]);
        }
    }

    // 區間查詢，半開區間 [l, r)
    Pair query(int l, int r) const {
        Pair res = {INT_MAX, INT_MIN};             // identity
        for (l += n, r += n; l < r; l >>= 1, r >>= 1) {
            if (l & 1) res = merge(res, tree[l++]);
            if (r & 1) res = merge(res, tree[--r]);
        }
        return res;
    }
};

int main() {
    vector<int> a = {3, 1, 4, 1, 5, 9, 2, 6};
    SegTree st(a);

    // 原本閉區間 [2, 5] => 半開 [2, 6)
    auto res = st.query(2, 6);
    cout << "min=" << res.first << " max=" << res.second << "\n";   // 1 9

    st.update(1, 10);   // a[1] = 10
    res = st.query(0, 3);   // 閉區間 [0,2] => 半開 [0,3)
    cout << "min=" << res.first << " max=" << res.second << "\n";   // 3 10
    return 0;
}

#if 0

'use strict';

const MAX_SAFE = Number.MAX_SAFE_INTEGER;
const MIN_SAFE = -Number.MAX_SAFE_INTEGER;

// 合併：取較小為 min、較大為 max
function merge(a, b) {
    return [Math.min(a[0], b[0]), Math.max(a[1], b[1])];
}

class SegTree {
    constructor(a) {
        this.n = a.length;
        // tree 大小 2n；葉子在 tree[n .. 2n-1]
        this.tree = Array.from({ length: 2 * this.n },
                               () => [MAX_SAFE, MIN_SAFE]);   // identity
        for (let i = 0; i < this.n; i++)
            this.tree[this.n + i] = [a[i], a[i]];            // 葉子
        for (let i = this.n - 1; i > 0; i--)                 // 由下往上 build
            this.tree[i] = merge(this.tree[i << 1],
                                 this.tree[(i << 1) | 1]);
    }

    // 單點更新 a[pos] = val
    update(pos, val) {
        pos += this.n;
        this.tree[pos] = [val, val];
        while (pos > 1) {                                    // 一路往上推到根
            pos >>= 1;
            this.tree[pos] = merge(this.tree[pos << 1],
                                   this.tree[(pos << 1) | 1]);
        }
    }

    // 區間查詢，半開區間 [l, r)
    query(l, r) {
        let res = [MAX_SAFE, MIN_SAFE];                      // identity
        for (l += this.n, r += this.n; l < r; l >>= 1, r >>= 1) {
            if (l & 1) res = merge(res, this.tree[l++]);
            if (r & 1) res = merge(res, this.tree[--r]);
        }
        return res;
    }
}

// ---- 測試 ----
const a = [3, 1, 4, 1, 5, 9, 2, 6];
const st = new SegTree(a);

// 原本閉區間 [2, 5] => 半開 [2, 6)
let res = st.query(2, 6);
console.log(`min=${res[0]} max=${res[1]}`);   // 1 9

st.update(1, 10);   // a[1] = 10
res = st.query(0, 3);   // 閉區間 [0,2] => 半開 [0,3)
console.log(`min=${res[0]} max=${res[1]}`);   // 3 10

#endif

