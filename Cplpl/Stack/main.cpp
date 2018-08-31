#include <iostream>

using namespace std;

//структура узла
struct Node{
    Node(int num) : data_(num), next_(0) {}

    int data_; //данные
    Node * next_; // указатель на следующий эл-т
};

struct Stack{
    Node * head_; //голова стека

    Stack () : head_(0) {}

    // показать голову
    void top() const {
        if( head_ != 0)
            cout << head_->data_ << endl;
        else
            cout << "No element" << endl;
    }

    //добавить элемент
    void push(int const num){
        Node * temp = new Node(num);
        temp->next_ = head_;
        head_ = temp;
    }

    //удалить элемент
    void pop(){
        Node * temp = head_;
        head_ = head_->next_;
        delete temp;
    }

};


int main()
{
    Stack test;

    test.top();

    test.push(5);

    test.top();

    test.push(7);

    test.top();

    test.push(13);

    test.top();

    test.pop();

    test.top();

    test.pop();

    test.top();

    test.pop();

    test.top();

    return 0;
}
