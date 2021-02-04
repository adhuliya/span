// Test case by Venkatesh
int *x,*y,*w,*z,**p,***q,a,b,c,**r;

void f(){
	x=&a;
	if(a) {
	  *p=w;
	   if(b)
	   	q=&r;
	}

    y=&b;
}


int main(){
	p=&y;
	w=&c;
	f();
  // p->{y}, w->{c}, x->{a}, y->{b}, z->{Null}, r->{Null}
  // q->{r, Null} or q->{Null} if condition is evaluated
}
