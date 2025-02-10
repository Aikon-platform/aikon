# 🤝 How to contribute

The VHS application is meant to be a framework usable but many research projects
interested in extracting visual elements from historical documents digitizations.
Thus, the different branches are used for different purposes

## Main branch

The main branch is dedicated to the version common for every project.
The code is meant to reflect a stable version of the application.
Developments are integrated to the main branch once all the contributors
agree to add the features to the common version.

## Prod branches

The branches containing `-prod` in their name corresponds to the versions of
the application used on production. They may slightly vary from the `main`
branch to fit the needs of a specific project. They hold to code that is deployed
on production servers

## Dev branches

Branches can be created to develop a specific feature (e.g. evolution of the data model),
it is then recommended to finish the development of the feature before merging it into the main branch
and deleting the branch.

One branch for each contributor can be used also to develop simultaneously several features
that can be merged as a batch into the main branch.

One commit should correspond to a complete modification into the codebase,
many small commits are better than few big commits.
