#include <iostream>
#include <string>

using namespace std;

// класс большое целое (беззнаковое)
class UBigInt{
public:
    // конструкторы
    UBigInt(){
        number_ = "0";
    }
    UBigInt(string const & str){
        number_ = str;
    }
    UBigInt(int const & a){
        number_= to_string(a);
    }

    // вывод в строку
    string toString() const{
        return number_;
    }

private:
    string number_;
};

// сложение двух больших целых
UBigInt operator + (UBigInt const & i1, UBigInt const & i2){
    string str1 = i1.toString();
    int l1 = str1.length();
    string str2 = i2.toString();
    int l2 = str2.length();

    string answer; // результирующая строка
    int checker = 0; // чекер увеличение разряда (число двузначное)

    for(int i = 0; i != max(l1, l2); ++i){
        int t1 = 0, t2 = 0, summa = 0;

        if(l1-1 - i >= 0)
            t1 = (int)str1[l1-1 - i] - '0';
        else
            t1 = 0;

        if(l2-1 - i >= 0)
            t2 = (int)str2[l2-1 - i] - '0';
        else
            t2 = 0;

        summa = t1 + t2 + checker;
        if(summa > 9){
            summa %= 10;
            checker = 1;
        }
        else
            checker = 0;

        answer = to_string(summa) + answer;

    }

    if (checker == 1)
        answer = to_string(1) + answer;

    return UBigInt(answer);
}

// алгоритм вычесления числа Фибоначчи

int main()
{
    int count;
    cin >> count;

    UBigInt pr = 0;
    UBigInt th = 1;

    cout << "i = 0\nFib = 0" << "\n";
    cout << "i = 1\nFib = 1" << "\n";

    for(int i = 2; i <= count; ++i){
        UBigInt temp = pr + th;
        pr = th;
        th = temp;

        cout << "i = " << i << "\n";
        cout << "Fib = " << th.toString() << "\n";
    }

//    cout << "Count = " << count << "\n" << "Fib = " << th.toString() << "\n";

    return 0;
}
