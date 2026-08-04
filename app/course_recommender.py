"""
Course Recommendation Module
"""

COURSE_MAP = {

    "python": [
        {
            "title": "Python for Everybody",
            "provider": "Coursera",
            "url": "https://www.coursera.org/specializations/python"
        },
        {
            "title": "Complete Python Bootcamp",
            "provider": "Udemy",
            "url": "https://www.udemy.com/course/complete-python-bootcamp/"
        }
    ],

    "java": [
        {
            "title": "Java Programming Masterclass",
            "provider": "Udemy",
            "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/"
        }
    ],

    "spring": [
        {
            "title": "Spring Boot Masterclass",
            "provider": "Udemy",
            "url": "https://www.udemy.com/course/spring-hibernate-tutorial/"
        }
    ],

    "spring boot": [
        {
            "title": "Spring Boot Masterclass",
            "provider": "Udemy",
            "url": "https://www.udemy.com/course/spring-hibernate-tutorial/"
        }
    ],

    "react": [
        {
            "title": "React - The Complete Guide",
            "provider": "Udemy",
            "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/"
        }
    ],

    "mysql": [
        {
            "title": "SQL for Data Analysis",
            "provider": "Coursera",
            "url": "https://www.coursera.org/learn/sql-for-data-science"
        }
    ],

    "sql": [
        {
            "title": "SQL for Data Analysis",
            "provider": "Coursera",
            "url": "https://www.coursera.org/learn/sql-for-data-science"
        }
    ],

    "machine learning": [
        {
            "title": "Machine Learning Specialization",
            "provider": "Coursera",
            "url": "https://www.coursera.org/specializations/machine-learning-introduction"
        }
    ],

    "docker": [
        {
            "title": "Docker Essentials",
            "provider": "Udemy",
            "url": "https://www.udemy.com/topic/docker/"
        }
    ],

    "aws": [
        {
            "title": "AWS Cloud Practitioner",
            "provider": "Coursera",
            "url": "https://www.coursera.org/learn/aws-cloud-practitioner-essentials"
        }
    ],

    "git": [
        {
            "title": "Git & GitHub",
            "provider": "Coursera",
            "url": "https://www.coursera.org/learn/introduction-git-github"
        }
    ]
}


def recommend_courses(missing_skills):

    recommendations = []

    added = set()

    for skill in missing_skills:

        key = skill.strip().lower()

        if key in COURSE_MAP:

            for course in COURSE_MAP[key]:

                identifier = (
                    course["title"],
                    course["provider"]
                )

                if identifier not in added:

                    recommendations.append(course)

                    added.add(identifier)

    return recommendations