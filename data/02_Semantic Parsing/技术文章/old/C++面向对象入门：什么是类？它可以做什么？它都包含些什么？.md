---
title: C++面向对象入门：什么是类？它可以做什么？它都包含些什么？
tags: [博客文章, c++]
description: '在C++中，**类**（class）是对象的蓝图或模板，用于定义一组数据和相关的操作。类是面向对象编程（OOP）的核心特性之一，它将数据（成员变量）和操作这些数据的函数（成员函数）封装在一起。类是创建对象的基础，类的实例称为**对象**。'
published: 2024-12-14T16:39:01
---

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

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

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

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

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
            cout << my_nature <<endl;
        }
private:
    string my_nature;
};
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

现在可以想象一个这样的场景！

有一只很谨慎的宝可梦，她不会随便告诉别人自己的性格，除非对方也告诉自己。某一天，有一只宝可梦调用了她的公有函数getNature，并且提供了自己的性格字符串，完成之后，这只谨慎的宝可梦也告诉对方自己的性格，于是他们成为了好朋友！

可喜可贺，可喜可贺。不过，这个过程是怎么实现的呢？

我们已经知道类的私有内容是不能被直接使用的，但我们可以提供函数让外部实现对内部的私有内容进行使用，例如进行输出操作。虽然别人不能使用私有内容，但类本身是可以使用自己的私有内容的。

我们补全main函数，试着看看这只谨慎的宝可梦会不会告诉我们自己的性格：

```cpp
int main()
{
	Pokemon togekiss;
	togekiss.getNature("大胆");
	return 0;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

输出结果：

![img](https://i-blog.csdnimg.cn/direct/64083fd81dca4d70a0aa7fac7fd4c0b1.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

显而易见，这只谨慎的宝可梦在知道了我们的性格后，最终还是告诉了你她的性格，现在就成为好朋友啦！

**不过，Pokmon(){}又是个什么鬼哇！这个函数怎么没有类型呢！**

# 三.构造函数

一般的函数其实是个很被动给的东西，就好比上面的getNature函数，如果不是外部主动的调用，永远也不会有人知道你的性格是什么。

那有没有什么不需要主动调用也能够产生效果的函数呢？

没错！就是——构造函数！

> C++ 中的 **构造函数**（Constructor）是一种特殊的成员函数，用于在创建对象时初始化对象的成员变量。构造函数的名称与类的名称相同，并且没有返回类型。它在对象被创建时自动调用，通常用于为对象的成员变量分配初始值。

当我们的类进行实例化变为对象后，它就自动的完成了构造函数，构造函数非常特殊，为了和其他函数做区分，它不仅没有返回值，而且函数名和类的名称完全相同。

在刚才的Pokemon(){}中，我们就对my_nature进行了初始化，让它的性格初始化为胆小。除了进行初始化，还可以执行一些功能，不过这部分就留给你自己探索吧！试试构造函数里都能写一些什么有趣的东西！

```cpp
#include<iostream>

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
            cout << my_nature <<endl;
        }
private:
    string my_nature;
};

int main()
{
	Pokemon togekiss;
	togekiss.getNature("大胆");
	cout << togekiss.attribute << endl;
	cout << togekiss.grade << endl;
	return 0;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

补全main函数，感受一下直接输出public内容和使用成员函数输出private内容的区别。

输出结果：

![img](https://i-blog.csdnimg.cn/direct/93d3e45dd884466ab6a6a07d00cf546f.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

# 四.拷贝构造函数

变量和变量之间的赋值相当容易，但对象和对象赋值就会麻烦很多，既然是copy，就需要有用来复制的对象，拷贝构造函数大概可以看成这样：

![img](https://i-blog.csdnimg.cn/direct/44d77ccbf97b46468c2895aa9890edfc.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

既然需要进行拷贝操作，那么新建立的对象就需要提供给一个对象才能调用拷贝构造函数，拷贝构造函数本身就必然需要一个对象参数才可以！

试着写一写：

现在有一个好奇的百变怪，它使用了变身技能，变化成了波克基斯的样子，于是就有了：

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
	Pokemon(const Pokemon &p)
	{
		grade = p.grade;
		attribute = p.attribute;
		my_nature = p.my_nature;
	}
    void getNature(string nature)
    {
        cout << my_nature <<endl;
    }
    friend void tellNature(Pokemon& p);
private:
    string my_nature;
};

void tellNature(Pokemon& p)
{
	cout << p.my_nature << endl;
}

int main()
{
	Pokemon togekiss;
	cout << togekiss.grade << endl;
	Pokemon ditto = togekiss;
	cout<< "百变怪的等级是：" << ditto.grade <<endl;
	return 0;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

在main函数中，输出了百变怪的等级，我们来看看吧：

![img](https://i-blog.csdnimg.cn/direct/ec9b948b30154a74b68e26d77cf56c20.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

现在，百变怪已经copy了波克基斯的各种特性了！

拷贝函数还分为浅拷贝函数和深拷贝函数，这个就留给大家自己研究啦~快进快进（冲刺冲刺）

# 五.析构函数

既然有实例化后立刻调用的函数，那根据对称定律（其实是我瞎编的）也会有与之相反效果的函数存在——没错！它就是析构函数。

比起构造函数（构造对象时调用的函数），析构函数从字面意思上似乎有些捉摸不清，这里不妨理解成“分崩离析时调用的函数”！这样理解就简单很多了，析构函数就是当对象被销毁时调用的函数。

> 析构函数（Destructor）是类的一个特殊成员函数，在对象生命周期结束时自动调用，用于释放对象占用的资源。它的主要作用是清理和销毁对象时进行资源的回收，避免资源泄漏（如内存泄漏、文件句柄泄漏等）。

析构函数的名称和类名称相同，并且不返回任何类型，也没有前缀...这不就成构造函数了吗！！

嘿嘿，这种低级的错误是不可能有的，和构造函数相比，析构函数会在前面加一个小波浪号。

```cpp
class Helicopter
{
public:
    Helicopter()
    {
        cout << "孩子们我会开直升机" << endl;
    }
    ~Helicopter()
    {
        cout << "manba out!";
    }
};
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

当Helicopter类的对象被delect释放掉的时候，就会调用析构函数。

main函数如下：

```cpp
int main()
{
	Helicopter* CXK = new Helicopter();
	delete CXK;
	return 0;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

欸，聪明的你突然发现，这里对对象进行实例的方式，和上次的togekiss的方法似乎不太一样：

```cpp
Helicopter* CXK = new Helicopter();
Pokemon togekiss;
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

**有什么区别？**

如果像形似变量声明的格式去实例对象，那么就会得到一个存在在栈上的对象，也就是局部对象。这一点和局部变量类似，当离开函数的时候，局部对象就会被销毁自动释放掉，不需要手动释放。

因为自动销毁的特性，因此栈对象不能使用delete销毁，只能等离开函数被自动释放，而析构函数则会在这个时候被调用。虽然栈对象用起来很容易，而且不用操心释放的问题，但却限制了灵活性，并且栈的空间十分有限，如果在栈上存在大量的栈对象，很有可能会出现栈溢出的情况！这对于程序来说是致命的！ 

所以我们需要——堆对象！

栈的大小一般只有几mb，而堆甚至可以有几个G，把对象放在栈里就好像百吨王开在石子路上，尤其是写成递归，栈完全受不了这种东西啦。

在c语言里，我们使用malloc关键字进行结构体变量的内存申请，而c++里只需要一个关键字new就可以了！

new关键字会自动分配内存，而我们也可以很方便的在想要销毁的地方使用delete销毁，灵活性很好！试着把togekiss写成堆对象试试吧！

# 六.友元函数

我真希望你还记得你的宝可梦朋友togekiss，但如果你想重复询问她的性格，就需要调用getNature函数，并且还要重复一遍自己的性格，对于朋友来说，是不是有点...太麻烦了？

试想一下，如果一个人很信任自己的朋友，也会把自己的小秘密分享给他。友元函数就是这样，它可以访问private的成员，并且它不是类的成员函数。

> 类的友元函数是定义在类外部，但有权访问类的所有私有（private）成员和保护（protected）成员。尽管友元函数的原型有在类的定义中出现过，但是友元函数并不是成员函数。

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
        cout << my_nature <<endl;
    }
    friend void tellNature(Pokemon& p);
private:
    string my_nature;
};

void tellNature(Pokemon& p)
{
	cout << p.my_nature << endl;
}

int main()
{
	Pokemon togekiss;
	tellNature(togekiss);
	return 0;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

现在Pokemon类中有友元函数了，事实上也许会有很多宝可梦，为了准确的获取具体的信息，我们应该告诉友元函数自己的目标对象，因此需要传递一个对象。

在这里，我们给tellNature函数了一个togekiss对象，它就能正确的调出togekiss的性格了！可以直接访问类的private，这就是友元函数的魔力。（所以说友谊是魔法啊！）

友元函数可以在不暴露类内部的具体情况的条件下就访问类内部的细节，在一定意义上可以增强灵活性。

好啦，现在，你和togekiss是真正的好朋友了，试着用写一个友元函数让她告诉你自己的等级吧。

# 七.特殊指针this

如果你写过JavaScript，一定对this不陌生，十分方便但是容易看头晕的关键字，它用于指向当前对象的实例。

> 在 C++ 中，`this` 指针是一个隐式的指针，它指向当前对象的地址。每当一个成员函数被调用时，`this` 指针会自动传递给成员函数，指向调用该成员函数的对象。你可以使用 `this` 指针来访问当前对象的成员变量和成员函数。

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
		cout<< this->name + " " + this->sex <<endl;
	}
};
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

小牛出生后，我们要在对象里记录这只牛的名字，肯定是构造函数啦。

勤劳的你又发现，类的变量名居然和构造函数传入的变量名一样，那这个时候要是能区分一下就好了。这时候，this指针就能发挥作用。它指向对象，能够完成赋值的操作，在下面的打印里，也尝试使用以下this指针来代替.吧！

# 八.小结

当然！类包含的东西可不仅仅只有这些，如果你继续学习，会接触到虚函数，静态成员，重载函数，重写函数，常量成员函数之类。

但无论如何，面向对象的种子已经扎根在你的知识库里了，接下来多上手写写东西吧！





如果你是资深的大佬，我很荣幸能让您读这一篇拙作，不管您有如何看法，我都很愿意接受您的批评指导。

如果你是和我差不多的学生，希望这篇文章能让你回忆起一些可能会疏漏掉的内容，能够帮助到你。

如果你是一点基础也没有的萌新，也没关系的，就算没看懂也要鼓励你，能一口气读这么多字已经很厉害了！！！加油，计算机的一切都是人类创造的，就和动漫的世界一样，这是多么浪漫的事情啊，相信你也一定能够用心创造魔法的！

如果只是看个乐呵，我也很高兴自己闲暇时写的东西能让人觉得眼前一亮。



# 附录

源代码：

```cpp
#include<iostream>

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
//        cout << my_nature <<endl;
//    }
//    friend void tellNature(Pokemon& p);
//private:
//    string my_nature;
//};
//
//void tellNature(Pokemon& p)
//{
//	cout << p.my_nature << endl;
//}
//
//int main()
//{
//	Pokemon togekiss;
////	togekiss.getNature("大胆");
////	cout << togekiss.attribute << endl;
//	cout << togekiss.grade << endl;
////	tellNature(togekiss);
//	Pokemon ditto = togekiss;
//	cout<< "百变怪的等级是：" << ditto.grade <<endl;
//	return 0;
//}

//class Helicopter
//{
//public:
//    Helicopter()
//    {
//        cout << "孩子们我会开直升机" << endl;
//    }
//    ~Helicopter()
//    {
//        cout << "manba out!";
//    }
//};
//
//int main()
//{
//	Helicopter* CXK = new Helicopter();
//	delete CXK;
//	return 0;
//}

class New_baby{
public:
	string name;
	string sex;
	New_baby(string name,string sex)
	{
		this->name = name;
		this->sex = sex;
		cout<< this->name + " " + this->sex <<endl;
	}
};

int main()
{
	New_baby* coco = new New_baby("coco","girl");
	return 0;
}
```
