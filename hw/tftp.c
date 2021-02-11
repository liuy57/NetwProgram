#include <arpa/inet.h> 
#include <netinet/in.h> 
#include <stdio.h> 
#include <stdlib.h> 
#include <string.h> 
#include <sys/socket.h> 
#include <sys/types.h> 
#include <unistd.h> 
#include <signal.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdbool.h> 
#include <signal.h>


#define BUFFER_SIZE 1024

int all_port[100] = { [ 0 ... 99 ] = -1 };


/* tftp opcode mnemonic */
enum opcode {
	RRQ=1,
	WRQ,
	DATA,
	ACK,
	ERROR
};

void sig_child(int signo){

	pid_t pid;
	int stat;

	//	pid = waitpid(-1,&stat,WNOHANG);
	while((pid= waitpid(-1,&stat,WNOHANG)) >0){
		printf("Child PID %d has terminated.\n",pid);
	}
}


// function to clear buffer
void clearBuf(char* b){
	for (int i = 0; i < BUFFER_SIZE; i++)
		b[i] = '\0';
}


int comp(const void * elem1, const void * elem2){
	int f = *((int*)elem1);
	int s = *((int*)elem2);
	if (f > s) return  1;
	if (f < s) return -1;
	return 0;
}


int send_ACK(int sockfd, char* content, int len, struct sockaddr_in* client_sock){
	ssize_t ret;
	ret = sendto(sockfd, content, len, 0, (struct sockaddr*) client_sock, sizeof(*client_sock));
	if(ret < 0){
		perror("ERROR! Sendto failed!\n");
	}
	return ret;
}




void printBuf(char *buffer){
	for(int i=0;i<BUFFER_SIZE;i++){
		printf("%x",buffer[i]);
	}
	printf("\n");
}

void RRQ_request(int sockfd, char* buffer, struct sockaddr_in* cl_sock, socklen_t cliaddr_len, int new_port){


	int block_count=0;
	char  msg[516];
	char  temp_buf[512];

	struct timeval timeout;
	timeout.tv_sec = 1;
	timeout.tv_usec = 0;

	if(setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0){
		perror("setsockopt failed\n");
		close(sockfd);
		exit(1);
	}

	//unsigned short int opcode; CHECK ME
	unsigned short int * opcode_ptr =(unsigned short int *)msg;


	FILE *fd;
	fd = fopen(buffer+2, "r");

	if (fd == NULL) {
		perror("ERROR! File can not be opened!\n");

		close(sockfd);
		fclose(fd);		

		exit(1);
	}

	while(1){

		//sending blocks
		block_count++;
		*opcode_ptr = htons(DATA);
		opcode_ptr[1] = htons(block_count);

		int r;
		if((r=fread(temp_buf,1,512,fd))>0){
			for(int i = 0 ;i<r;i++){
				msg[i+4] = temp_buf[i];
			}
		}else{ // no bytes left => transmission complete
			break;
		}
		//printBuf(msg);

		int c = sendto(sockfd, msg, r+4, 0,(struct sockaddr *) cl_sock, cliaddr_len);
		printf("[DEBUG] %d bytes sent in block %d\n",c,block_count);


	//	if(new_port != ntohs(cl_sock->sin_port)){
	//		*opcode_ptr = htons(ERROR);
	//		*(opcode_ptr+1) = htons(5);
	//		*(buffer+4) = 0;
	//		c = sendto(sockfd, buffer, 5, 0, (struct sockaddr *)cl_sock, cliaddr_len);
	//		continue;
	//	}

		//recv ACK

		int timeout_count=10;
		int i = 0;
		for( i=timeout_count;i>=0;i-- ){
			c = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr *) cl_sock, &cliaddr_len);
			if (c!=4){//1 sec passed without recving ACK => handle retransmission
				int c = sendto(sockfd, msg, r+4, 0,(struct sockaddr *) cl_sock, cliaddr_len);
				printf("[DEBUG] Retransmitted %d bytes sent in block %d, retransmission #%d\n",c,block_count, i+1);
			}
			if(c==4){ //TODO: if we never reach here, handle timeout
				printf("[DEBUG] recvd ACK!\n");
				break;
			}
		}
		if (i < 0) {
			perror("ERROR! Timed out!\n");

			close(sockfd);
			fclose(fd);			

			exit(1);
		}
	}

	close(sockfd);
	fclose(fd);
}

void WRQ_request(int sockfd, char* buffer, struct sockaddr_in* cl_sock, socklen_t cliaddr_len, int new_port){


	char buff_data[BUFFER_SIZE];

	struct timeval timeout;
	timeout.tv_sec = 1;
	timeout.tv_usec = 0;

	if(setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0){
		perror("setsockopt failed\n");
			close(sockfd);

		exit(1);
	}

	unsigned short int opcode;
	unsigned short int * opcode_ptr =(unsigned short int *)buffer;


	FILE *fd;
	fd = fopen(buffer+2, "w");

	if (fd == NULL) {
		perror("ERROR! File can not be opened!\n");

		close(sockfd);
		fclose(fd);

		exit(1);
	}

	*opcode_ptr = htons(ACK);
	*(opcode_ptr + 1) = htons(0);

	int data_len = send_ACK(sockfd, buffer, 4, cl_sock);
	if(data_len < 0){
		perror("ERROR! ACK was not send to client!\n");

		close(sockfd);
		fclose(fd);

		exit(1);
	}



	int count = 10;
	//int rev_len; CHECK ME

	int i;
	int not_close = 1;
	int c;
	int block_number = 0;


	opcode = ntohs(*opcode_ptr);


	while (not_close) {

		for (i = count; i>=0; i--) {

			c = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr *) cl_sock, &cliaddr_len);

			if(c < 0){
				//  perror("recvfrom");

				close(sockfd);
				fclose(fd);

				exit(-1);
			}

			if (c >= 0 && c < 4) {
				printf("message with invalid size received\n");
				*opcode_ptr = htons(ERROR);
				*(opcode_ptr+1) = htons(5);
				*(buffer+4) = 0;
				c = sendto(sockfd, buffer, 5, 0, (struct sockaddr *)cl_sock, cliaddr_len);

				close(sockfd);
				fclose(fd);				

				exit(1);
			}

			if (c >= 4) {
				break;
			}


			if (c < 516) {
				//	printf("%s\n", "clsoe!!!");
				not_close = 0;
				//   break;
			}

			if (errno != EAGAIN) {
				printf("transfer killed\n");

				close(sockfd);
				fclose(fd);

				exit(1);
			}


			//	opcode = htons(ACK);
			c = send_ACK(sockfd, buffer, 4, cl_sock);

			if (c < 0) {
				printf("transfer killed 2\n");

				close(sockfd);
				fclose(fd);

				exit(1);
			}

		//	if(new_port != ntohs(cl_sock->sin_port)){
		//		*opcode_ptr = htons(ERROR);
		//		*(opcode_ptr+1) = htons(5);
		//		*(buffer+4) = 0;
		//		c = sendto(sockfd, buffer, 5, 0, (struct sockaddr *)cl_sock, cliaddr_len);
		//		continue;
		//	}
		}


		if (!i) {
			printf("transfer timed out\n");

			close(sockfd);
			fclose(fd);

			exit(1);
		}

		block_number++;


		if (ntohs(opcode) == ERROR)  {
			printf("error message received\n");

			close(sockfd);
			fclose(fd);

			exit(1);
		}

		if (ntohs(*opcode_ptr) != DATA)  {
			*opcode_ptr = htons(ERROR);
			*(opcode_ptr+1) = htons(5);
			*(buffer+4) = 0;
			c = sendto(sockfd, buffer, 5, 0, (struct sockaddr *)cl_sock, cliaddr_len);
			printf("invalid message during transfer received\n");

			close(sockfd);
			fclose(fd);

			exit(1);
		}



		buffer[c] = '\0';
		//	   fprintf(fd, "%s\n", buffer+4);
		c = fwrite(buffer+4, 1, c-4, fd);



		if (c < 0) {
			perror("server: fwrite()");

			close(sockfd);
			fclose(fd);

			exit(1);
		}


		*opcode_ptr = htons(ACK);
		*(opcode_ptr+1) = htons(block_number);


		c = send_ACK(sockfd, buffer, 4, cl_sock);

		if (c < 0) {
			printf("transfer killed 3\n");

			close(sockfd);
			fclose(fd);

			exit(1);
		}

		for(int j = 0; j < BUFFER_SIZE; j++)
			buffer[j] = buff_data[j];


		c = sendto(sockfd, buffer, 4, 0, (struct sockaddr *)cl_sock, cliaddr_len);



	}


	close(sockfd);
	fclose(fd);
}



// driver code
int main(int argc, char **argv){

	if (argc != 3) {
		printf("usage:invalid arguments.\n");
		exit(1);
	}

	int start_port = atoi(argv[1]);
	int end_port = atoi(argv[2]);


	for (int i = 0 ; i < end_port-start_port; i++){
		all_port[i] = start_port + i + 1;
	}

	/*	for(int i=0; i<100; ++i){
		printf("%d\n", all_port[i]);
		}*/

	//	qsort(all_port, sizeof(all_port)/sizeof(*all_port), sizeof(*all_port), comp);

	int sockfd;
	struct sockaddr_in	servaddr;
	sockfd = socket(AF_INET, SOCK_DGRAM, 0);
	socklen_t servaddr_len = sizeof(servaddr);
	bzero(&servaddr, servaddr_len);
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(atoi(argv[1]));


	int binded = bind(sockfd, (struct sockaddr *) &servaddr, servaddr_len);

	if (sockfd < 0){
		perror("ERROR! Sock failed!\n");
		exit(1);
	}
	if (binded != 0){
		perror("ERROR! Bind failed!\n");
		exit(1);
	}

	char buffer[BUFFER_SIZE];
	unsigned short int opcode;
	unsigned short int * opcode_ptr;

	int num_bytes;
	signal(SIGCLD, (void *) sig_child);

	/*	struct sigaction kill;
		kill.sa_handler = sig_child;
		sigemptyset(&kill.sa_mask);
		kill.sa_flags = 0;
		sigaction(SIGCHLD, &kill, NULL);*/


	getsockname(sockfd, (struct sockaddr *)&servaddr, &servaddr_len);
	printf("Listening to Port %d\n", ntohs(servaddr.sin_port));



	bool begin = false;

	int new_port = 0;

	struct sockaddr_in client_sock;


	while (1) {

		
		socklen_t len = sizeof(client_sock);	

		num_bytes = recvfrom(sockfd, buffer, BUFFER_SIZE, 0, (struct sockaddr*)&client_sock, &len);
		//	printf("%d\n",num_bytes);

		if (num_bytes < 0) {
		//	if(errno == EINTR) break;
			perror("recvfrom\n");
			exit(-1);
		}

		//struct sockaddr_in client_sock; CHECK ME
		//socklen_t cliaddr_len = sizeof(client_sock); CHECK ME
		//ssize_t len; CHECK ME

		//message read into buffer by this point
		opcode_ptr = (unsigned short int *)buffer;
		opcode = ntohs(*opcode_ptr);


		if (opcode == RRQ || opcode == WRQ){


			//	qsort(all_port, sizeof(all_port)/sizeof(*all_port), sizeof(*all_port), comp);
			int index = 0;
			while(index<end_port-start_port-1 && all_port[index]==-1){
				index++;
			}
			if(all_port[index]!=-1){
				printf("index: %d\n", index);
				new_port = all_port[index];
				all_port[index] = -1;
			}
			else{
				perror("%s.%u: No port to use \n");
				exit(1);
			}


			// spawn a child process to handle the request
			if(fork() == 0){
				close(sockfd);
				begin = true;
				break;
			}
		}
	}

	if(begin==true){


		printf("The new port is: %d\n", new_port);

		struct sockaddr_in clientaddr;
		sockfd = socket(AF_INET,SOCK_DGRAM,0);
		if (sockfd < 0){
			perror("ERROR! Sock failed!\n");
			exit(1);
		}
		clientaddr.sin_family      = AF_INET;
		clientaddr.sin_addr.s_addr = htonl(INADDR_ANY);
		clientaddr.sin_port        = htons(new_port);
		socklen_t alen = sizeof(clientaddr);

		int b = bind(sockfd, (struct sockaddr *) &clientaddr, alen);
		if (b < 0){
			perror("ERROR! Bind failed!\n");
			exit(1);
		}

		if(opcode == RRQ){

			printf("start RRQ!\n");
			RRQ_request(sockfd,buffer,&client_sock,alen,new_port);
		}
		else if(opcode == WRQ){

			printf("start WRQ !\n");
			WRQ_request(sockfd, buffer, &client_sock, alen, new_port);

		}
	}


	close(sockfd);

	return 0;
}
