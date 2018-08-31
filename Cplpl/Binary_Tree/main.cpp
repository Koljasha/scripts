#include <iostream>
#include <queue>

using namespace std;

// структура узла
struct Node{
    int data_;
    Node * left_;
    Node * right_;

    Node(int data, Node * left = NULL, Node * right = NULL) : data_(data), left_(left), right_(right) {}
};

// синоним указателя
typedef Node * pNode;


// структура дерева
struct Tree{
    // конструктор
    Tree() : root_(NULL) {}

    //деструктор
    ~Tree(){
        remove(root_);
    }

    // вернуть корень
    pNode Root() const{
        return root_;
    }

    // добавление величины
    void add_value(int a, pNode & root){
        if(root == NULL){
            root = new Node(a);
        }
        else if(root->data_ > a){
            add_value(a, root->left_);
        }
        else if(root->data_ < a){
            add_value(a, root->right_);
        }
    }

    // добавление велечины (для удобства без указания указателя)
    void add_value(int a){
        add_value(a, root_);
    }

    // вывод дерева (упорядоченный ряд 1 3 8 15 20 ...)
    void print_tree(pNode root) const{
        if(root != NULL){
            print_tree(root->left_);
            cout << root->data_ << " ";
            print_tree(root->right_);
        }
    }

    // вывод от корня
    void print_tree_from_root(pNode root) const{
        queue<pNode> que;
        que.push(root);
        while(que.empty() == false){
            pNode temp = que.front();
            que.pop();
            cout << temp->data_ << " ";
            if(temp->left_ != NULL)
                que.push(temp->left_);
            if(temp->right_ != NULL)
                que.push(temp->right_);
        }
    }

    // вывод дерева (для удобства без указания указателя)
    void print_tree() const{
        print_tree(root_);
        cout << endl;
        print_tree_from_root(root_);
        cout << endl;
    }

    //удаление дерева
    void remove(pNode root){
        if(root != NULL){
            remove(root->left_);
            remove(root->right_);
            delete root;
        }
    }

private:
        pNode root_;
};


int main()
{
    Tree tree;
    tree.add_value(7);
    tree.add_value(15);
    tree.add_value(25);
    tree.add_value(2);
    tree.add_value(3);
    tree.add_value(13);
    tree.add_value(1);
    tree.add_value(5);

    tree.print_tree();

    return 0;
}
