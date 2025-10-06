#include <stdio.h>

int gcd(int a, int b){
    if(a == 0 || b == 0){
        return 1;
    } else {
        return gcd(b, a % b);
    }
}

int main(){
    int a, b, result;
    printf("Enter the first NUmber : \n");
    scanf("%d", &a);
    printf("Enter the second number : \n");
    scanf("%d", &b);
   
    if(a > b) {
        result = gcd(a, b);
    } else {
        result = gcd(b, a);
    }
    printf("The gcf of the two numbers is : %d \n", result);

    return 0;
}