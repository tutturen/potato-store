# Potato Store backend
An e-commerce system made in TDT4242 Adv. Software Development

## What stack is this?

This backend is written in Django + Graphene-Django.
Django is used for database structures, while Graphene serves a GraphQL interface to the database.
The frontend is allowed to choose what information it needs from a certain query through GraphQL.

As an example, this is a query for the price of a shopping cart while getting some information on the products:

    query {
        cart(products: [1, 2, 3]) {
            total
            totalDiscount
            products {
                name
                subtitle
                price
            }
        }
    }

## How to run it locally?

First, you need to install `pip`. This project was written against Python 3.6.
It is not guaranteed to work with lower versions.
Verify that you are running a `pip` version for Python 3.x by running:

    pip --version
        
On some platforms, the Python 3.x version of `pip` may be called `pip3` instead.

Installation of `pip` is not covered in this document.
In general, it is available through Linux package managers
and Brew on OS X, and is bundled by default with Python 3.x on Windows. 

### Installing dependencies

When `pip` is present, you may install `pipenv` by running

    pip install pipenv
        
Followed by the dependency step

    cd src/ # From the base of the git repository
    pipenv install

If `pipenv` is not found, it typically has not been added to your `PATH` environment variable.
Platform-specific instructions vary in this case.

### Running the Django server

Django is controlled through the `./manage.py` file, which exposes several commands, but the following are relevant:

    runserver - run the server locally, by default on localhost:8000
    migrate   - applies changes made to database structures to the current database,
                 also creates the tables if the do not exist
    loaddata  - using provided data fixtures, add some dummy data to the database

A typical run would be done by (when starting in the git source directory):

    cd src/
    pipenv shell
    ./manage.py loaddata ./products/fixtures/products.json
    ./manage.py migrate
    ./manage.py runserver

When the server is up, you can interact with it at several endpoints:

 - `/admin`   - Django administrator panel
 - `/graphql` - GraphiQL interface for doing queries directly against the database
 - `/`        - Mostly just help

### Relevant source files

Most of the code done in this project can be found in:

 - `src/products/models.py` - Django models, persistent data structures for the database
 - `src/products/schema.py` - Exposing Django models to GraphQL along with validation
 - `src/products/admin.py`  - Data definition for Django's administrator panel
 
