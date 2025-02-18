from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker,relationship
engine = create_engine("sqlite:///example.db", echo=True)
Base = declarative_base()
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    orders= relationship("Order", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', age={self.age})"
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    user = relationship("User", back_populates="orders")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
user1 = User(name="Alice", age=25)
user2 = User(name="Bob", age=30)

session.add(user1)
session.add(user2)
session.commit()  # Saves to the database

print(f"Inserted Users: {user1}, {user2}")
order1 = Order(user_id=user1.id, amount=100)
order2 = Order(user_id=user1.id, amount=150)
order3 = Order(user_id=user2.id, amount=200)

session.add_all([order1, order2, order3])
session.commit()

print(f"Inserted Orders: {order1}, {order2}, {order3}")
users = session.query(User).all()
for user in users:
    print(user)

# Fetch the user by name
alice = session.query(User).filter_by(name="Alice").first()

# Update age
if alice:
    alice.age = 26
    session.commit()  # Save changes
    print(f"Updated Alice: {alice}")

# Fetch Bob's first order
bob_order = session.query(Order).filter(Order.user_id == user2.id).first()

# Update the amount
if bob_order:
    bob_order.amount = 250
    session.commit()
    print(f"Updated Order: {bob_order}")

