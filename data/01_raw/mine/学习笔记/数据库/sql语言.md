---
title: sql语言
tags: [数据库]
category: 学习
published: 2025-06-22T13:40:42
---

# SQL语言

## 创建表

创建表的基本语法：

```sql
Create table <表名>（<列名><数据类型>[列级完整性约束条件]，
  <列名><数据类型>[列级完整性约束条件]， 
  … 
  [，<表级完整性约束条件>]）；
```

示例：创建学生成绩表SC

```sql
Create table sc (
  Sno char (9)，
  Cno char (4),
  Grade smallint,
  Primary key(sno,cno),   -- 设置主码，由两个属性构成
  Foreign key(sno) references student(sno)  -- 设置外码，参照student表
)
```

## 修改表结构

```sql
-- 新增一列
Add[column] <新列名> <数据类型>[完整性约束]

-- 删除一列
Drop[column] <列名> [cascade|restrict]
```

## 删除基本表

```sql
Drop table <表名> [cascade/restrict]
```

> 如果选择restrict删除，则该表的删除是有限制条件的，想删除的基本表不能被其他表的约束引用，也不能有视图，触发器等，如果存在这些依赖关系，则表不能删除。

## 索引的建立

```sql
Create [UNIQUE][CLUSTER] index <索引名> on <表明>（<列名>[[次序]]）；
```

> **数据字典**：是管理系统内部的一组系统表，记录了所有的定义信息

## 单表查询

查询指定列：

```sql
Select 列名 from 表名;
```

也能是一个表达式：

```sql
Select sname, 2024-sage from student
```

### 取消重复的行

使用 `DISTINCT` 关键字。

### 条件查询（WHERE）

- **比较大小**：查询所有年龄在20岁以下的学生的姓名和年龄

```sql
Select name, age from student where age < 20;
```

- **确定范围**：查询年龄在20~30岁之间的学生的姓名、系别和年龄

```sql
Select name, sdept, age from student where age between 20 and 30;
```

- **确定集合**：谓词 `IN` 能用来查询属性值属于指定集合的元组

```sql
-- 查询cs系，ma系学生的姓名和性别
Select name, sex from student where sdept in ('cs','ma');
```

### 字符匹配（LIKE）

- `%` 代表任意长度的字符串
- `_` 代表单个字符

```sql
-- 查询所有姓张的学生的学号，姓名和性别
Select id, name, sex from student where name like '张%';

-- 查询所有名字里第二个字为阳的学生的学号和姓名
Select id, name from student where name like '_阳%';
```

### 查询空值

```sql
-- 查询缺少成绩的学生的学号和相应的课程
Select id, cno from sc where grade is null;
```

### 多条件查询

```sql
-- 查询计算机系年龄在20岁以下的学生姓名
Select name from student where sdept='cs' and age<20;
```

### 排序（ORDER BY）

```sql
-- 查询全体学生的情况，结果按照系名升序排列，同一系按年龄降序
Select * from student Order by sdept asc, age desc
```

## 聚集函数

SQL提供的主要聚集函数：
- `COUNT` 统计
- `SUM` 求和
- `AVG` 平均（必须是数值型）
- `MAX` 最大值
- `MIN` 最小值

```sql
-- 查询学生的总数
Select count(*) from student;

-- 计算选修1号课程的学生的平均成绩
Select avg(grade) from sc where cno='1';

-- 查询选修1号课程的学生最高分数
Select max(grade) from sc where cno='1';
```

### 分组（GROUP BY）

`GROUP BY` 字句用于分组，`HAVING` 短语用于指定筛选条件：

```sql
-- 查询各个课程号和相应的选课人数
Select cno, count(sno) from sc group by cno;

-- 查询选修三门以上课程的学生学号
Select sno from sc group by sno having count(*)>3;
```

## 连接查询

### 等值连接

```sql
-- 查询每个学生及选修课程的情况
Select student.*, sc.* from student, sc where student.sno = sc.sno;
```

### 自身连接

```sql
-- 查询course表中一门课的间接先行课
Select first.cno, second.cpno 
from course first, course second 
where first.cpno = second.cno;
```

### 外连接

如果想保留不满足条件的元组，需要使用外连接。

```sql
Select 属性名 
from 表1 left/right outer join 表2 
on 表1.属性名 = 表2.属性名
```

**通俗示例**：

```sql
-- 邀请名单表
CREATE TABLE 邀请名单 (
  姓名 VARCHAR(50),
  邀请函编号 VARCHAR(10) PRIMARY KEY
);

-- 实际到场表
CREATE TABLE 实际到场 (
  姓名 VARCHAR(50),
  签到编号 VARCHAR(10) PRIMARY KEY
);

-- 左外连接：列出左边关系中所有的元组
Select * from 邀请名单 left join 实际到场 on 邀请名单.姓名 = 实际到场.姓名;

-- 右外连接：列出右边关系中所有的元组
Select * from 邀请名单 right join 实际到场 on 邀请名单.姓名 = 实际到场.姓名;
```

> 当涉及多表连接时，不同表可能有同名字段。明确列出属性，加上表名前缀（像 `Student.Sno`），能清晰区分不同表的字段，避免歧义。

### 多表连接

```sql
-- 查询每个学生的学号，姓名，选修的课和成绩
Select student.sno, sname, cname, grade 
from student, sc, course 
where student.sno = sc.sno and course.cno = sc.cno;
```

## 嵌套查询

一个 `SELECT-FROM-WHERE` 语句称为一个查询块，将一个查询块嵌套在另一个的 `WHERE` 字句或 `HAVING` 短语的条件中的查询，称之为嵌套查询。

### 基本嵌套查询

```sql
-- 查询与刘晨在同一个系的学生
Select sno, sname, sdept 
from student 
where sdept in (
  Select sdept from student where sname='刘晨'
);
```

### 带有比较运算符的子查询

```sql
-- 查询所有选修了信息系统和数学课程，并且成绩均不及格的学生的学号
Select sno from student 
where sno in (
  select sno from course, sc 
  where course.cno = sc.cno and cname = '信息系统' and grade < 60
) 
and sno in (
  select sno from course, sc 
  where course.cno = sc.cno and cname = '数学' and grade < 60
)
```

## 数据更新

### 插入数据

```sql
Insert into 表名[属性列1, 属性列2…] values (常量1, 常量2…);
```

```sql
-- 将一个新学生元组插入student表中
Insert into student (sno, sname, sex, sdept, sage) 
values ('005', '张三', '男', 'is', 18);
```

插入查询结果：

```sql
Insert into dept_age(sdept, avg_age) 
select sdept, avg(sage) from student group by sdept;
```

### 更新数据

```sql
-- 将学生1145的年龄改为25
Update student set sage = 25 where sno='1145';

-- 将所有入学时间为2024年的学生的年龄改为22岁
Update student set sage = 22 where sentry_year='2024';

-- 将所有学生的年龄增加1岁
Update student set sage = sage + 1;
```

### 删除数据

```sql
Delete from 表名 where 条件
```

> `DELETE` 删除元组和数据，但不删除定义和字典，只会清空数据。不带 `WHERE` 相当于清除全部数据。