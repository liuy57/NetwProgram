#include <stdio.h> 
#include <stdlib.h> 
#include <string.h> 
#include <sys/socket.h> 
#include <sys/types.h> 
#include <unistd.h> 
#include <stdbool.h> 
#include <time.h>
#include <ctype.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <errno.h> 

# define MAX_CLIENT 5
# define BUF_SIZE 1024




struct Client{
    char* name;
};


int counting_word(char* file_name){
	FILE *fd;
	fd = fopen(file_name, "r");
	char c; 
	int count = 0; 
	while((c = fgetc(fd)) != EOF){ 
		if(c == ' ' || c == '\n'){ 
			++count; 
		} 
	} 
	fclose(fd); 
	return count;
}

void generate_word(char* file_name, char* buffer, int max_len, int index){
	FILE *fp;
	int pos = 0;
	int len;
	if ((fp = fopen(file_name, "r")) == NULL){
		printf("Could not open myinputfile.txt\n");
		exit(1);
	}
	while ( !feof(fp)){
		if(fgets(buffer,max_len,fp) != NULL){
			 len = strlen(buffer);
			 buffer[len-1] = '\0'; 
			 if(pos==index-1){
			 	for(int i=0; i<len; ++i){
			 		buffer[i]=tolower(buffer[i]);
			 	}
			 	fclose(fp);
			 	return;
			 }
			 pos++;
	 	}
	}
	fclose(fp);
}


int main(int argc, char **argv){


	setvbuf( stdout, NULL, _IONBF, 0 );


	if (argc != 5) {
		printf("usage:invalid arguments.\n");
		exit(1);
	}

	int seed = atoi(argv[1]);
	int port = atoi(argv[2]);
	char* dict_file = argv[3];
	int max_len = atoi(argv[4]);
	int word_count = counting_word(dict_file);
	srand(seed);
	int index = rand()%word_count;
	char buffer[max_len];
	generate_word(dict_file,buffer,max_len,index);
	int word_len = strlen(buffer);

	struct Client client_name[MAX_CLIENT];
    for (int i = 0; i < MAX_CLIENT; i++){
        struct Client client;
        client.name = (char*)"";
        client_name[i] = client;
        printf("^%s^\n", client_name[i].name);
    }

	int					i, maxi, maxfd, listenfd, connfd, sockfd;
	int					nready, client[FD_SETSIZE];
	ssize_t				n;
	fd_set				rset, allset;
	char				buf[MAX_CLIENT];
	socklen_t			clilen;
	struct sockaddr_in	cliaddr, servaddr;

	int option = 1;
	sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if(sockfd == -1){ 
        printf("socket failed\n"); 
        exit(0); 
    } 
    if(setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &option, sizeof(option))<0){ 
        perror("setsockopt failed\n"); 
        exit(0); 
    } 
	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(port);

    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr))<0){   
        perror("bind failed");   
        exit(0);   
    }   
    printf("Listener on port %d \n", port); 

	if(listen(sockfd, MAX_CLIENT)< 0){   
        perror("listen");   
        exit(0);   
    } 

	maxfd = sockfd;			/* initialize */
	maxi = -1;					/* index into client[] array */
	for (i = 0; i < FD_SETSIZE; i++){
		client[i] = -1;			/* -1 indicates available entry */
	}
	FD_ZERO(&allset);
	FD_SET(sockfd, &allset);
/* end fig01 */

	char* message = "Welcome to Guess the Word, please enter your username.\n";   
    int num_client = 0;



/* include fig02 */
	for ( ; ; ) {

		rset = allset;		/* structure assignment */
		nready = select(maxfd+1, &rset, NULL, NULL, NULL);

        if ((nready < 0) && (errno!=EINTR)){   
            printf("select error"); 
            exit(0);  
        } 
		if (FD_ISSET(sockfd, &rset)){	/* new client connection */
			clilen = sizeof(cliaddr);
			connfd = accept(sockfd,(struct sockaddr *)&cliaddr, (socklen_t*)&clilen);

            if (connfd<0){   
                perror("accept");   
                exit(0);   
            } 
            //inform user of socket number - used in send and receive commands  
            printf("New connection , socket fd is %d , ip is : %s , port : %d \n" , connfd , inet_ntoa(cliaddr.sin_addr) , ntohs(cliaddr.sin_port));   






            bool out=false;


            char name_copy[500];

            for( ; ; ){       
	            //send new connection greeting message  
	            if( send(connfd, message, strlen(message), 0) != strlen(message) )   
	            {   
	                perror("send");   
	            }   
	                 
	            puts("Welcome message sent successfully"); 

            	
				// get the name
				char name[500];
				int namelen;
				label:
                if((namelen = recv(connfd, name, 500, 0)) < 0){
                    perror("name error");
                }
                //check whether the name exists
                name[namelen-1] = '\0';
                printf("name: %s\n", name);
                printf("len: %d\n", namelen);

                for(int i = 0; i < MAX_CLIENT; i++){

					if(strcmp(client_name[i].name,name)==0){
                	printf("#client_name[%d]: %s\n",i, client_name[i].name);
                	printf("#client_name: %s, name: %s\n", client_name[i].name, name);
	                	char msg[BUF_SIZE];
	                	sprintf(msg, "Username %s is already taken, please enter a different username\n", name);
			            if(send(connfd, msg, strlen(msg), 0) != strlen(msg)){   
			                perror("send");   
			            }
			            goto label;
                    }
                    else if(strlen(client_name[i].name)==0){
                    	printf("%s\n", "empty!\n");
                    	memset(name_copy,0,strlen(name_copy));
                    	strcpy(name_copy,name);
                    	printf("name_copy: %s\n", name_copy);
                    	char msg[BUF_SIZE];
                    	sprintf(msg, "Let's start playing, %s\n", name);
			            if(send(connfd, msg, strlen(msg), 0) != strlen(msg)){   
			                perror("send");   
			            } 	                    	
                    	out = true;
                    	break;
                    }
                }
                if(out==true){
                	break;
                }     
            }
 

         
            for( i=0; i < MAX_CLIENT; i++){
				
				if(client[i]<0){
					struct Client cli;
				//	char tmp[sizeof(name_copy)];
					char* tmp = (char *) malloc(125*sizeof(char));
					strcpy(tmp, name_copy);
					cli.name = tmp;
					client_name[i] = cli;
				//	free(tmp);
					printf("** %d ***%s\n", i, client_name[i].name);
					num_client++;
					char msg[BUF_SIZE];
					sprintf(msg, "There are %d player(s) playing. The secret word is %d letter(s).\n", num_client, word_len);
					if(send(connfd, msg, strlen(msg), 0) != strlen(msg)){   
						perror("send");   
					} 	
					break;
				}
			}

			for (i = 0; i < MAX_CLIENT; i++){

				if (client[i] < 0){
					client[i] = connfd;	/* save descriptor */
					break;
				}
				if (i == MAX_CLIENT){
					perror("too many clients");
				}
				FD_SET(connfd, &allset);	/* add new descriptor to set */
				if (connfd > maxfd){
					maxfd = connfd;			/* for select */
				}
				if (i > maxi){
					maxi = i;				/* max index in client[] array */
				}
				if (--nready <= 0){
					continue;				/* no more readable descriptors */
				}
			}

		}



		for(int j=0; j<5;++j){
            printf("client_name[%d] after change: %s\n", j, client_name[j].name);
            printf("client[%d] after change: %d\n", j, client[j]);
		}




	}

	return 0;
}



