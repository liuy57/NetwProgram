#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h> 




struct Number{
  int a;
  int b;
  int sum;
};


void* add(void* args){
	struct Number* n = (struct Number*)args;
    printf("Thread %ld running add() with [%d + %d]\n", pthread_self(), n->a, n->b); 
    n->sum = n->a + n->b;
    return (void*)n; 
} 


int main(int argc, char **argv){

	if(argc!=2){
		perror("Wrong argument!");
		exit(-1);
	}

	int MAX_ADDAND = atoi(argv[1]);
	int combination = MAX_ADDAND*(MAX_ADDAND-1);
	int tid_p = pthread_self();
    struct Number* args;
	pthread_t children[combination+1];
	struct Number* all[combination+1];

	for(int i=1; i<MAX_ADDAND; ++i){
		for(int j=1; j<=MAX_ADDAND; ++j){
		    pthread_t tid; 
		    args = (struct Number*)malloc(sizeof(struct Number));
		    all[(i-1)*MAX_ADDAND+j] = args;
		    args->a = i;
		    args->b = j;
		    args->sum = 0;
		    int val = pthread_create(&tid, NULL, add, args);
		    if(val<0){
		    	return -1;
		    }
		    else{
			    printf("Main starting thread add() for [%d + %d]\n", i, j);
		    	children[(i-1)*MAX_ADDAND+j] = tid;
		    }
		}
	}

	sleep(1);
	for(int i=1; i<=combination; ++i){
		struct Number* ret;
		pthread_join(children[i], (void*)&ret);
    	printf("In main, collecting thread %ld computed [%d + %d] = %d\n", children[i], ret->a, ret->b, ret->sum);
    	free(all[i]);
    }
    return 0; 
}















