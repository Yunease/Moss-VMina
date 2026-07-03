# 简单的自我介绍：

ciallo米娜桑，这里是琴泠，一个多平台活跃的在读本科生。在大多数人的印象里，编程是一个很难而且很枯燥的事情。不过，只要你掌握了良好的自学方法也一定能感受到来自计算机的乐趣！

一个人突发奇想写的专栏，内容可能会有错误得地方，请大家多多批评指正！这个专栏是面向一些对编程感兴趣，但是不知道怎么入坑的宅友，写的会很浅！也可以当作闲暇时候图一乐的东西看。废话不多，直接开始吧！

（默认你学过c或者c++语法基础）

# 一.什么是类：

在C++中，**类**（class）是对象的蓝图或模板，用于定义一组数据和相关的操作。类是面向对象编程（OOP）的核心特性之一，它将数据（成员变量）和操作这些数据的函数（成员函数）封装在一起。类是创建对象的基础，类的实例称为**对象**。

类是一个抽象的东西，就好比说是汽车，而对象则是具体的对象，例如 车牌号为xxx的车（聪明的你一定会知道，类会描述性质，也包含了车牌号，只要对车牌号等东西进行赋值，就能把抽象的类变为具体的实例，这个东西第一次理解可能会比较麻烦，自己上手写写会好理解一点）

是不是有点复杂，不过没关系的，面向对象是一种利好于人类思维的编程方式，理解起来会很容易，有点像c语言的结构体，我们来写一个简单的类：

类的关键字是class，后面跟类的名字，后接大括号来作为类的详细部分。

```cpp
class Pokemon
{
    //略
};
```

我们定义了一个名为宝可梦（没错！就是那个神奇宝贝！）的类，接下来需要填充的就是宝可梦的性质，例如等级，性格，属性等，于是如下：

```cpp
class Pokemon
{
public:
    int grade;
    string attribute;
private:
    string nature;
};
```

哎，是不是有什么不同？为什么变量分为了public和private呢，这些东西又是做什么的呢？

# 二.类也是有隐私的！

> 在C++中，`public` 和 `private` 是访问修饰符，用来指定类中成员（变量和函数）的访问权限。

定义大概是这样！这两个词都是高中3500里的重点词汇，相信大家都不陌生

public即为公有的，在类里意味着其下的所有变量和函数，都可以随便被类外边的东西调用。就好像在宝可梦战斗的时候，你能够看到对手宝可梦的等级和属性一样，即便这只宝可梦不属于你，你也能够访问到一些信息。

而pirvate则是私有的，意味着其下的所有内容都是不能直接被外部访问的，就好像对手备选的精灵，不能够直接访问到，只能在对方主动放出来的时候才能知道。

**有什么用？**

数据也是需要保护的，防止不合适的修改，只能通过指定的接口进行操作，保证了数据不会出错。

就好比：

```cpp
class Pokemon 
{
public:
    int grade;
    string attribute;
    Pokemon()
    {
    	my_nature = "胆小";
	}
    void getNature(string nature)
        {
            cout  C++ 中的 **构造函数**（Constructor）是一种特殊的成员函数，用于在创建对象时初始化对象的成员变量。构造函数的名称与类的名称相同，并且没有返回类型。它在对象被创建时自动调用，通常用于为对象的成员变量分配初始值。

当我们的类进行实例化变为对象后，它就自动的完成了构造函数，构造函数非常特殊，为了和其他函数做区分，它不仅没有返回值，而且函数名和类的名称完全相同。

在刚才的Pokemon(){}中，我们就对my_nature进行了初始化，让它的性格初始化为胆小。除了进行初始化，还可以执行一些功能，不过这部分就留给你自己探索吧！试试构造函数里都能写一些什么有趣的东西！

```cpp
#include

using namespace std;

class Pokemon 
{
public:
    int grade;
    string attribute;
    Pokemon()
    {
    	my_nature = "胆小";
    	grade = 100;
    	attribute = "妖精 飞行";
	}
    void getNature(string nature)
        {
            cout  析构函数（Destructor）是类的一个特殊成员函数，在对象生命周期结束时自动调用，用于释放对象占用的资源。它的主要作用是清理和销毁对象时进行资源的回收，避免资源泄漏（如内存泄漏、文件句柄泄漏等）。

析构函数的名称和类名称相同，并且不返回任何类型，也没有前缀...这不就成构造函数了吗！！

嘿嘿，这种低级的错误是不可能有的，和构造函数相比，析构函数会在前面加一个小波浪号。

```cpp
class Helicopter
{
public:
    Helicopter()
    {
        cout  类的友元函数是定义在类外部，但有权访问类的所有私有（private）成员和保护（protected）成员。尽管友元函数的原型有在类的定义中出现过，但是友元函数并不是成员函数。

在Pokemon类中加入友元函数试试：

```cpp
class Pokemon 
{
public:
    int grade;
    string attribute;
    Pokemon()
    {
    	my_nature = "胆小";
    	grade = 100;
    	attribute = "妖精 飞行";
	}
    void getNature(string nature)
    {
        cout  在 C++ 中，`this` 指针是一个隐式的指针，它指向当前对象的地址。每当一个成员函数被调用时，`this` 指针会自动传递给成员函数，指向调用该成员函数的对象。你可以使用 `this` 指针来访问当前对象的成员变量和成员函数。

Pokemon的类写的有点太多了，我们暂时不用它，来写个New_baby类吧。

试想一下，在玩星露谷物语的时候，你养的牛生了一头小牛，新生命的诞生真是一件令人欢喜的事情，不过为了登记在信息栏里，我们需要知道这头小牛的一些信息：

```cpp
class New_baby{
public:
	string name;
	string sex;
	New_baby(string name,string sex)
	{
		this->name = name;
		this->sex = sex;
		coutname + " " + this->sex 

using namespace std;

//class Pokemon 
//{
//public:
//    int grade;
//    string attribute;
//    Pokemon()
//    {
//    	my_nature = "胆小";
//    	grade = 100;
//    	attribute = "妖精 飞行";
//	}
//	Pokemon(const Pokemon &p)
//	{
//		grade = p.grade;
//		attribute = p.attribute;
//		my_nature = p.my_nature;
//	}
//    void getNature(string nature)
//    {
//        cout name = name;
		this->sex = sex;
		coutname + " " + this->sex <<endl;
	}
};

int main()
{
	New_baby* coco = new New_baby("coco","girl");
	return 0;
}
```