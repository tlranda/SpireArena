Contributions are welcome as this is a small personal project, so these guidelines are intentionally flexible and informal.
That said, it is much easier to work with external collaborators under a consistent basis, so it is recommended to make a best effort to follow these guidelines.

General Community Expecations:
* This is a personal project, not a job. Nothing is at stake here--constructive criticism is welcome, but be mindful of the tone you use.
* Flexibility is expected on your part as well as that of maintainers. Assume the best in others and work to make ends meet.
* There should be no reason whatsoever for any material associated to this project to be controversial or offensive to any reasonable person. Keep it that way.

Writing Helpful Issues:
* The library is in an extremely early stage of development, so many issues may be ignored or dismissed due to project scope or development timelines.
* Issues more likely to be addressed include bug reports for older implemented functionality and identifying bottlenecks or pythonic issues with the repository.
* As should be common practice for any open-source project, search the open and closed issues to see if a similar issue has already been created by another user. Adding commentary and information or proper reference to prior issues is always helpful.
* Use a short, clear and descriptive title to identify your problem and help others with similar experiences to locate your issue.
* When possible, always include a minimum working example and the branch/commit hash you are working off of for replicability. Code in the style of `demo.py` with a fixed seed for replication is best suited for demonstration purposes.
* Explain the difference between what you experience and what you believe should have occurred instead.

Writing Helpful Pull Requests:
* Conforming to existing principles and conventions (see below) makes it much easier to review and incorporate revisions.
* Provide actual commit messages with substantive information about what you are changing and why.
* Unless specifically requested or authorized, large scale refactors and rewrites are best left to your own repository and will not be considered.
* Use a short, clear and descriptive title to identify what the request addresses. Limit the changes in your request to this material.
* Reference relevant issues if they exist in your title or description.

Code Principles and Conventions:
* Classes begin with capital letters, and library-level helper functions begin with lowercase letters. Both use CamelCase rather than Under_Scores for word separation.
* Naming conventions for internal libary components are more flexible but should be consistent within contributions and match the style of similar code, especially as an extension.
* Abstract classes should handle as much generalizeable material as possible to increase consistency and reduce code bloat and bug opportunities.
* Implementing classes should rely on abstract superclasses heavily. If you need something novel in an implemented class, ask yourself if other classes may use it. If so, the code may be better suited at the abstract class level, even if this requires refactoring.
* Internal classes are best served by helper functions to make lookup and usage more consistent and transparent to end users.
* Use the settings module for global package controls and synchronized data, such as debug checks. Especially during prototype phases of implementation, more debug at the DEBUG.full level is preferable.
* Unless you have good reason, exhaust keyword arguments in library function calls as these signatures do change from time to time. Explicitly listing all keywords makes it easier to trace code that needs to be updated when such changes occur, which limits bugs from being introduced.
