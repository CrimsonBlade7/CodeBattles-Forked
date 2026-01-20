"""
constants.py

This file stores constant values that don't change while the program runs.
We use it to keep our main code clean and to make it easy to find and update
things like game rules or, in this case, the coding problems.
"""

# A list of dictionaries, where each dictionary represents a coding problem card.
PROBLEM_TEMPLATES = [
    {
        'problem': {
            'title': 'Two Sum',
            'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
            'difficulty': 'Easy',
            'functionSignature': 'def twoSum(nums: list, target: int) -> list:',
            'testCases': [
                {'input': {'nums': [2, 7, 11, 15], 'target': 9}, 'expectedOutput': [0, 1]},
                {'input': {'nums': [3, 2, 4], 'target': 6}, 'expectedOutput': [1, 2]},
                {'input': {'nums': [3, 3], 'target': 6}, 'expectedOutput': [0, 1]}
            ]
        },
        # The reward applied when the player solves this problem.
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 30}
    },
    {
        'problem': {
            'title': 'Valid Parentheses',
            'description': 'Given a string s containing just the characters "(", ")", "{", "}", "[" and "]", determine if the input string is valid.',
            'difficulty': 'Easy',
            'functionSignature': 'def isValid(s: str) -> bool:',
            'testCases': [
                {'input': {'s': '()'}, 'expectedOutput': True},
                {'input': {'s': '()[]{}'}, 'expectedOutput': True},
                {'input': {'s': '(]'}, 'expectedOutput': False}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 25},
        'challenge': {'type': 'time_limit', 'value': 120}
    },
    {
        'problem': {
            'title': 'Merge Two Sorted Lists',
            'description': 'Merge two sorted linked lists and return it as a sorted list.',
            'difficulty': 'Easy',
            'functionSignature': 'def mergeTwoLists(list1: list, list2: list) -> list:',
            'testCases': [
                {'input': {'list1': [1, 2, 4], 'list2': [1, 3, 4]}, 'expectedOutput': [1, 1, 2, 3, 4, 4]},
                {'input': {'list1': [], 'list2': []}, 'expectedOutput': []}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'other', 'effect': 'remove_time', 'value': 20}
    },
    {
        'problem': {
            'title': 'Longest Palindromic Substring',
            'description': 'Given a string s, return the longest palindromic substring in s.',
            'difficulty': 'Medium',
            'functionSignature': 'def longestPalindrome(s: str) -> str:',
            'testCases': [
                {'input': {'s': 'babad'}, 'expectedOutput': 'bab'},
                {'input': {'s': 'cbbd'}, 'expectedOutput': 'bb'}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 45},
        'challenge': {'type': 'complexity', 'value': 'O(n)'}
    },
    {
        'problem': {
            'title': 'Container With Most Water',
            'description': 'Find two lines that together with the x-axis forms a container, such that the container contains the most water.',
            'difficulty': 'Medium',
            'functionSignature': 'def maxArea(height: list) -> int:',
            'testCases': [
                {'input': {'height': [1, 8, 6, 2, 5, 4, 8, 3, 7]}, 'expectedOutput': 49},
                {'input': {'height': [1, 1]}, 'expectedOutput': 1}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'all', 'effect': 'remove_time_all', 'value': 30}
    },
    {
        'problem': {
            'title': '3Sum',
            'description': 'Find all triplets in the array which gives the sum of zero.',
            'difficulty': 'Medium',
            'functionSignature': 'def threeSum(nums: list) -> list:',
            'testCases': [
                {'input': {'nums': [-1, 0, 1, 2, -1, -4]}, 'expectedOutput': [[-1, -1, 2], [-1, 0, 1]]},
                {'input': {'nums': []}, 'expectedOutput': []}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'targeted', 'effect': 'remove_time_targeted', 'value': 50},
        'challenge': {'type': 'line_limit', 'value': 30}
    },
    {
        'problem': {
            'title': 'Trapping Rain Water',
            'description': 'Given n non-negative integers representing an elevation map, compute how much water it can trap after raining.',
            'difficulty': 'Hard',
            'functionSignature': 'def trap(height: list) -> int:',
            'testCases': [
                {'input': {'height': [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]}, 'expectedOutput': 6},
                {'input': {'height': [4, 2, 0, 3, 2, 5]}, 'expectedOutput': 9}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 60}
    },
    {
        'problem': {
            'title': 'Longest Increasing Subsequence',
            'description': 'Find the length of the longest strictly increasing subsequence.',
            'difficulty': 'Hard',
            'functionSignature': 'def lengthOfLIS(nums: list) -> int:',
            'testCases': [
                {'input': {'nums': [10, 9, 2, 5, 3, 7, 101, 18]}, 'expectedOutput': 4},
                {'input': {'nums': [0, 1, 0, 3, 2, 3]}, 'expectedOutput': 4}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 45},
        'challenge': {'type': 'time_limit', 'value': 180}
    },
    {
        'problem': {
            'title': 'Binary Search',
            'description': 'Given a sorted array of integers and a target value, return the index of the target if found, otherwise return -1.',
            'difficulty': 'Medium',
            'functionSignature': 'def binarySearch(nums: list, target: int) -> int:',
            'testCases': [
                {'input': {'nums': [-1, 0, 3, 5, 9, 12], 'target': 9}, 'expectedOutput': 4},
                {'input': {'nums': [-1, 0, 3, 5, 9, 12], 'target': 2}, 'expectedOutput': -1},
                {'input': {'nums': [5], 'target': 5}, 'expectedOutput': 0}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'targeted', 'effect': 'flashbang_targeted', 'value': 1}
    }
]
